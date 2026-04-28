"""Sign evidence packages with HMAC-SHA256 for integrity verification."""

import hashlib
import hmac
import json
import os
from pathlib import Path

from .models import EvidencePackage


def sign_package(pkg: EvidencePackage, secret: str | None = None) -> EvidencePackage:
    """Sign an evidence package with HMAC-SHA256.

    Uses SIGNING_SECRET env var if no secret is provided.
    For production, use a GitHub Actions secret.
    """
    if secret is None:
        secret = os.environ.get("SIGNING_SECRET", "devsecops-dev-signing-key")

    payload = _canonical_payload(pkg)
    sig = hmac.new(
        secret.encode("utf-8"),
        payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    pkg.signature = sig
    return pkg


def verify_package(pkg: EvidencePackage, secret: str | None = None) -> bool:
    """Verify the HMAC signature on an evidence package."""
    if not pkg.signature:
        return False
    if secret is None:
        secret = os.environ.get("SIGNING_SECRET", "devsecops-dev-signing-key")

    d = pkg.to_dict()
    sig = d.pop("signature", None)
    payload = json.dumps(d, sort_keys=True, default=str, separators=(",", ":"))

    expected = hmac.new(
        secret.encode("utf-8"),
        payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, sig)


def _canonical_payload(pkg: EvidencePackage) -> str:
    """Produce a canonical JSON representation for signing."""
    d = pkg.to_dict()
    d.pop("signature", None)
    return json.dumps(d, sort_keys=True, default=str, separators=(",", ":"))
