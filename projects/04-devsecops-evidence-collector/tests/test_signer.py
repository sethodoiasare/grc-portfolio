"""Tests for HMAC signing and verification."""

import os
import json
from pathlib import Path
from src.signer import sign_package, verify_package
from src.models import EvidencePackage

SAMPLE_DIR = Path(__file__).resolve().parent.parent / "data" / "sample_outputs"


def make_pkg() -> EvidencePackage:
    from src.packager import build_package
    return build_package(project="sign-test", branch="main", commit_sha="def456")


class TestSignPackage:
    def test_adds_signature(self):
        pkg = make_pkg()
        assert pkg.signature is None
        signed = sign_package(pkg, secret="test-key")
        assert signed.signature is not None
        assert len(signed.signature) == 64  # SHA256 hex

    def test_deterministic_signing(self):
        pkg1 = make_pkg()
        pkg2 = make_pkg()
        pkg2.evidence_package_id = pkg1.evidence_package_id
        pkg2.generated_at = pkg1.generated_at

        s1 = sign_package(pkg1, secret="test-key")
        s2 = sign_package(pkg2, secret="test-key")
        assert s1.signature == s2.signature

    def test_different_secret_different_sig(self):
        pkg1 = make_pkg()
        pkg2 = make_pkg()
        pkg2.evidence_package_id = pkg1.evidence_package_id
        pkg2.generated_at = pkg1.generated_at

        s1 = sign_package(pkg1, secret="key-a")
        s2 = sign_package(pkg2, secret="key-b")
        assert s1.signature != s2.signature

    def test_env_var_secret(self):
        os.environ["SIGNING_SECRET"] = "env-test-key"
        pkg = make_pkg()
        signed = sign_package(pkg)  # uses env var
        assert signed.signature is not None
        del os.environ["SIGNING_SECRET"]


class TestVerifyPackage:
    def test_valid_signature(self):
        pkg = make_pkg()
        signed = sign_package(pkg, secret="verify-key")
        assert verify_package(signed, secret="verify-key")

    def test_invalid_signature(self):
        pkg = make_pkg()
        signed = sign_package(pkg, secret="key-a")
        assert not verify_package(signed, secret="key-b")

    def test_no_signature(self):
        pkg = make_pkg()
        assert pkg.signature is None
        assert not verify_package(pkg)

    def test_tampered_package(self):
        pkg = make_pkg()
        signed = sign_package(pkg, secret="tamper-key")
        signed.project = "tampered-value"
        assert not verify_package(signed, secret="tamper-key")

    def test_tampered_findings(self):
        pkg = make_pkg()
        signed = sign_package(pkg, secret="tamper-key2")
        signed.findings_summary.sast["critical"] = 999
        assert not verify_package(signed, secret="tamper-key2")


class TestRoundTrip:
    def test_sign_and_verify(self):
        pkg = make_pkg()
        signed = sign_package(pkg, secret="roundtrip")
        assert verify_package(signed, secret="roundtrip")

    def test_json_roundtrip(self, tmp_path):
        """Verify that JSON serialization preserves signature validity."""
        pkg = make_pkg()
        signed = sign_package(pkg, secret="json-rt")

        f = tmp_path / "pkg.json"
        f.write_text(json.dumps(signed.to_dict(), default=str))

        data = json.loads(f.read_text())
        sig = data.pop("signature", None)
        rehydrated = EvidencePackage(**{k: v for k, v in data.items() if k != "signature"})
        rehydrated.signature = sig

        assert verify_package(rehydrated, secret="json-rt")
