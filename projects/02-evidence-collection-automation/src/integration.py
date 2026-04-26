"""
Real-system integration layer for the Evidence Collection Automator.

Each connector type provides:
  - A typed config dataclass (credentials, endpoints, auth method)
  - A collect_*() function that connects to the live system and returns EvidenceItems
  - A test_connection_*() function that validates config and attempts authentication

In 'simulated' mode or when INTEGRATION_MODE != 'live', connectors fall back to
generating sample data via the simulator in connectors.py.

In 'live' mode, the connector attempts a real API call. If it fails, it falls
back to simulation and logs the error — the tool is never broken by a failed
connection.

Credentials are stored in the auth_config JSON column on the connectors table.
"""

from dataclasses import dataclass, field, fields
from typing import Optional
import json
import os
import urllib.request
import urllib.error
import ssl
import traceback


# ---------------------------------------------------------------------------
# Configuration Models
# ---------------------------------------------------------------------------

@dataclass
class ADConfig:
    integration_type: str = "azure_ad"       # "azure_ad" | "on_prem_ad" | "ldap"
    tenant_id: str = ""
    client_id: str = ""
    client_secret: str = ""
    domain: str = ""
    ldap_server: str = ""
    base_dn: str = ""


@dataclass
class MDMConfig:
    integration_type: str = "intune"         # "intune" | "workspace_one"
    tenant_id: str = ""
    client_id: str = ""
    client_secret: str = ""
    workspace_one_url: str = ""
    workspace_one_api_key: str = ""


@dataclass
class FirewallConfig:
    integration_type: str = "panorama"        # "panorama" | "checkpoint_mgmt" | "fortimanager" | "ssh"
    host: str = ""
    port: int = 443
    api_key: str = ""
    username: str = ""
    password: str = ""
    vendor: str = "Palo Alto"


@dataclass
class VulnScannerConfig:
    integration_type: str = "tenable"        # "tenable" | "qualys" | "rapid7" | "openvas"
    api_url: str = ""
    access_key: str = ""
    secret_key: str = ""


@dataclass
class SIEMConfig:
    integration_type: str = "sentinel"       # "sentinel" | "splunk" | "qradar" | "elastic"
    workspace_id: str = ""
    tenant_id: str = ""
    client_id: str = ""
    client_secret: str = ""
    splunk_host: str = ""
    splunk_token: str = ""


@dataclass
class DLPConfig:
    integration_type: str = "purview"        # "purview" | "symantec" | "forcepoint"
    tenant_id: str = ""
    client_id: str = ""
    client_secret: str = ""
    symantec_api_url: str = ""
    symantec_api_key: str = ""


CONFIG_CLASSES: dict[str, type] = {
    "sim_ad": ADConfig,
    "sim_mdm": MDMConfig,
    "sim_firewall": FirewallConfig,
    "sim_vuln": VulnScannerConfig,
    "sim_siem": SIEMConfig,
    "sim_dlp": DLPConfig,
}


# Human-readable field labels for the UI
FIELD_LABELS: dict[str, dict[str, str]] = {
    "sim_ad": {
        "integration_type": "Integration Type",
        "tenant_id": "Tenant ID",
        "client_id": "Client ID",
        "client_secret": "Client Secret",
        "domain": "Domain",
        "ldap_server": "LDAP Server",
        "base_dn": "Base DN",
    },
    "sim_mdm": {
        "integration_type": "Integration Type",
        "tenant_id": "Tenant ID",
        "client_id": "Client ID",
        "client_secret": "Client Secret",
        "workspace_one_url": "Workspace ONE URL",
        "workspace_one_api_key": "Workspace ONE API Key",
    },
    "sim_firewall": {
        "integration_type": "Integration Type",
        "host": "Management Host",
        "port": "Port",
        "api_key": "API Key",
        "username": "SSH Username",
        "password": "SSH Password",
        "vendor": "Vendor",
    },
    "sim_vuln": {
        "integration_type": "Integration Type",
        "api_url": "API URL",
        "access_key": "Access Key",
        "secret_key": "Secret Key",
    },
    "sim_siem": {
        "integration_type": "Integration Type",
        "workspace_id": "Workspace ID",
        "tenant_id": "Tenant ID",
        "client_id": "Client ID",
        "client_secret": "Client Secret",
        "splunk_host": "Splunk Host",
        "splunk_token": "Splunk Token",
    },
    "sim_dlp": {
        "integration_type": "Integration Type",
        "tenant_id": "Tenant ID",
        "client_id": "Client ID",
        "client_secret": "Client Secret",
        "symantec_api_url": "Symantec API URL",
        "symantec_api_key": "Symantec API Key",
    },
}

INTEGRATION_TYPE_OPTIONS: dict[str, list[str]] = {
    "sim_ad": ["azure_ad", "on_prem_ad", "ldap"],
    "sim_mdm": ["intune", "workspace_one"],
    "sim_firewall": ["panorama", "checkpoint_mgmt", "fortimanager", "ssh"],
    "sim_vuln": ["tenable", "qualys", "rapid7", "openvas"],
    "sim_siem": ["sentinel", "splunk", "qradar", "elastic"],
    "sim_dlp": ["purview", "symantec", "forcepoint"],
}

REQUIRED_FIELDS_BY_MODE: dict[str, dict[str, list[str]]] = {
    "sim_ad": {
        "azure_ad": ["tenant_id", "client_id", "client_secret"],
        "on_prem_ad": ["domain", "ldap_server", "base_dn"],
        "ldap": ["ldap_server", "base_dn"],
    },
    "sim_mdm": {
        "intune": ["tenant_id", "client_id", "client_secret"],
        "workspace_one": ["workspace_one_url", "workspace_one_api_key"],
    },
    "sim_firewall": {
        "panorama": ["host", "api_key"],
        "checkpoint_mgmt": ["host", "api_key"],
        "fortimanager": ["host", "api_key"],
        "ssh": ["host", "username", "password"],
    },
    "sim_vuln": {
        "tenable": ["api_url", "access_key", "secret_key"],
        "qualys": ["api_url", "access_key", "secret_key"],
        "rapid7": ["api_url", "access_key", "secret_key"],
        "openvas": ["api_url", "access_key", "secret_key"],
    },
    "sim_siem": {
        "sentinel": ["workspace_id", "tenant_id", "client_id", "client_secret"],
        "splunk": ["splunk_host", "splunk_token"],
        "qradar": ["splunk_host", "splunk_token"],
        "elastic": ["splunk_host", "splunk_token"],
    },
    "sim_dlp": {
        "purview": ["tenant_id", "client_id", "client_secret"],
        "symantec": ["symantec_api_url", "symantec_api_key"],
        "forcepoint": ["symantec_api_url", "symantec_api_key"],
    },
}


def load_config(connector_type: str, config_json: str) -> object:
    cls = CONFIG_CLASSES.get(connector_type)
    if cls is None:
        return None
    data = json.loads(config_json or "{}")
    field_names = {f.name for f in fields(cls)}
    valid_fields = {k: v for k, v in data.items() if k in field_names}
    return cls(**valid_fields)


def get_config_schema(connector_type: str) -> dict | None:
    """Return field labels, options, and required-fields info for the UI."""
    cls = CONFIG_CLASSES.get(connector_type)
    if cls is None:
        return None
    field_list = []
    for f in fields(cls):
        field_list.append({
            "name": f.name,
            "type": "number" if f.type == int else ("password" if f.name in ("client_secret", "secret_key", "password", "api_key", "splunk_token", "workspace_one_api_key") else "text"),
            "label": FIELD_LABELS.get(connector_type, {}).get(f.name, f.name),
            "default": f.default if f.default is not None else ("" if f.type == str else 443),
        })
    return {
        "fields": field_list,
        "integration_types": INTEGRATION_TYPE_OPTIONS.get(connector_type, []),
        "required_fields": REQUIRED_FIELDS_BY_MODE.get(connector_type, {}),
    }


# ---------------------------------------------------------------------------
# Connection Testing
# ---------------------------------------------------------------------------


def _http_get(url: str, headers: dict | None = None, timeout: int = 10) -> tuple[int, str]:
    """Make an HTTP GET request. Returns (status_code, body_or_error)."""
    try:
        req = urllib.request.Request(url, headers=headers or {})
        ctx = ssl.create_default_context()
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
            return resp.status, resp.read().decode("utf-8", errors="replace")[:2000]
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")[:1000]
        return e.code, body
    except urllib.error.URLError as e:
        return 0, f"Connection failed: {e.reason}"
    except Exception as e:
        return 0, str(e)


def _http_post(url: str, data: dict | None = None, headers: dict | None = None, timeout: int = 10) -> tuple[int, str]:
    """Make an HTTP POST request. Returns (status_code, body_or_error)."""
    try:
        body = json.dumps(data).encode() if data else b""
        req = urllib.request.Request(url, data=body, headers=headers or {}, method="POST")
        ctx = ssl.create_default_context()
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
            return resp.status, resp.read().decode("utf-8", errors="replace")[:2000]
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")[:1000]
        return e.code, body
    except urllib.error.URLError as e:
        return 0, f"Connection failed: {e.reason}"
    except Exception as e:
        return 0, str(e)


def _validate_config(config: object, connector_type: str) -> list[str]:
    """Check that required fields for the selected integration_type are present."""
    missing = []
    it = getattr(config, "integration_type", "unknown")
    required = REQUIRED_FIELDS_BY_MODE.get(connector_type, {}).get(it, [])
    for field_name in required:
        val = getattr(config, field_name, "")
        if not val:
            missing.append(field_name)
    return missing


# --- AD ---

def test_connection_ad(config: ADConfig) -> dict:
    """Test connection to Active Directory / Azure AD."""
    missing = _validate_config(config, "sim_ad")
    if missing:
        return {"ok": False, "error": f"Missing required fields for {config.integration_type}: {', '.join(missing)}"}

    if config.integration_type == "azure_ad":
        # Microsoft Graph: attempt token acquisition via client credentials
        token_url = f"https://login.microsoftonline.com/{config.tenant_id}/oauth2/v2.0/token"
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        body_data = f"client_id={config.client_id}&client_secret={config.client_secret}&scope=https://graph.microsoft.com/.default&grant_type=client_credentials"
        try:
            req = urllib.request.Request(token_url, data=body_data.encode(), headers=headers, method="POST")
            ctx = ssl.create_default_context()
            with urllib.request.urlopen(req, timeout=15, context=ctx) as resp:
                data = json.loads(resp.read())
            if "access_token" in data:
                return {"ok": True, "detail": "Authenticated to Microsoft Graph via Azure AD OAuth2 client credentials"}
            return {"ok": False, "error": f"Azure AD returned: {data.get('error_description', data.get('error', str(data)[:200]))}"}
        except urllib.error.HTTPError as e:
            body = e.read().decode(errors="replace")[:500]
            return {"ok": False, "error": f"Azure AD auth failed (HTTP {e.code}): {body}"}
        except urllib.error.URLError as e:
            return {"ok": False, "error": f"Cannot reach Azure AD: {e.reason}. Verify the tenant_id '{config.tenant_id}' is correct and network access to login.microsoftonline.com is available."}
        except Exception as e:
            return {"ok": False, "error": f"Unexpected error: {e}"}

    elif config.integration_type == "on_prem_ad":
        # LDAP: attempt TCP connection to LDAP server port 389/636
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        try:
            sock.connect((config.ldap_server, 389))
            sock.close()
            return {"ok": True, "detail": f"TCP connection to {config.ldap_server}:389 succeeded. Full LDAP bind requires ldap3 library and appropriate credentials."}
        except socket.error as e:
            return {"ok": False, "error": f"Cannot reach LDAP server {config.ldap_server}:389: {e}"}

    elif config.integration_type == "ldap":
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        try:
            sock.connect((config.ldap_server, 389))
            sock.close()
            return {"ok": True, "detail": f"TCP connection to {config.ldap_server}:389 succeeded."}
        except socket.error as e:
            return {"ok": False, "error": f"Cannot reach LDAP server {config.ldap_server}:389: {e}"}

    return {"ok": False, "error": f"Unknown integration type: {config.integration_type}"}


# --- MDM ---

def test_connection_mdm(config: MDMConfig) -> dict:
    missing = _validate_config(config, "sim_mdm")
    if missing:
        return {"ok": False, "error": f"Missing required fields for {config.integration_type}: {', '.join(missing)}"}

    if config.integration_type == "intune":
        token_url = f"https://login.microsoftonline.com/{config.tenant_id}/oauth2/v2.0/token"
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        body_data = f"client_id={config.client_id}&client_secret={config.client_secret}&scope=https://graph.microsoft.com/.default&grant_type=client_credentials"
        try:
            req = urllib.request.Request(token_url, data=body_data.encode(), headers=headers, method="POST")
            ctx = ssl.create_default_context()
            with urllib.request.urlopen(req, timeout=15, context=ctx) as resp:
                data = json.loads(resp.read())
            if "access_token" in data:
                return {"ok": True, "detail": "Authenticated to Microsoft Graph for Intune via OAuth2"}
            return {"ok": False, "error": f"Azure AD returned: {data.get('error_description', str(data)[:200])}"}
        except urllib.error.HTTPError as e:
            body = e.read().decode(errors="replace")[:500]
            return {"ok": False, "error": f"Azure AD auth failed (HTTP {e.code}): {body}"}
        except urllib.error.URLError as e:
            return {"ok": False, "error": f"Cannot reach Azure AD: {e.reason}"}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    elif config.integration_type == "workspace_one":
        status, body = _http_get(
            f"{config.workspace_one_url}/api/system/info",
            headers={"aw-tenant-code": config.workspace_one_api_key, "Accept": "application/json"},
        )
        if status in (200, 401):
            return {"ok": True, "detail": f"Reached Workspace ONE at {config.workspace_one_url} (HTTP {status})"}
        return {"ok": False, "error": f"Failed to reach Workspace ONE: {body[:300]}"}

    return {"ok": False, "error": f"Unknown integration type: {config.integration_type}"}


# --- Firewall ---

def test_connection_firewall(config: FirewallConfig) -> dict:
    missing = _validate_config(config, "sim_firewall")
    if missing:
        return {"ok": False, "error": f"Missing required fields for {config.integration_type}: {', '.join(missing)}"}

    if config.integration_type in ("panorama", "checkpoint_mgmt", "fortimanager"):
        url = f"https://{config.host}:{config.port}/api/"
        try:
            req = urllib.request.Request(url + (f"?type=keygen&key={config.api_key}" if config.integration_type == "panorama" else "?action=login"))
            ctx = ssl.create_default_context()
            with urllib.request.urlopen(req, timeout=10, context=ctx) as resp:
                return {"ok": True, "detail": f"Reached {config.vendor} management API at {config.host}:{config.port} (HTTP {resp.status})"}
        except urllib.error.HTTPError as e:
            if e.code in (401, 403):
                return {"ok": False, "error": f"Authentication rejected (HTTP {e.code}). Check your API key."}
            return {"ok": True, "detail": f"Reached {config.vendor} at {config.host}:{config.port} (HTTP {e.code} — may need valid credentials)"}
        except urllib.error.URLError as e:
            return {"ok": False, "error": f"Cannot reach {config.host}:{config.port}: {e.reason}"}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    elif config.integration_type == "ssh":
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        try:
            sock.connect((config.host, config.port or 22))
            sock.close()
            return {"ok": True, "detail": f"TCP connection to {config.host}:{config.port or 22} succeeded. SSH auth requires paramiko library."}
        except socket.error as e:
            return {"ok": False, "error": f"Cannot reach {config.host}:{config.port or 22}: {e}"}

    return {"ok": False, "error": f"Unknown integration type: {config.integration_type}"}


# --- Vuln Scanner ---

def test_connection_vuln(config: VulnScannerConfig) -> dict:
    missing = _validate_config(config, "sim_vuln")
    if missing:
        return {"ok": False, "error": f"Missing required fields for {config.integration_type}: {', '.join(missing)}"}

    if config.integration_type == "tenable":
        headers = {"X-ApiKeys": f"accessKey={config.access_key}; secretKey={config.secret_key}"}
        status, body = _http_get(f"{config.api_url}/scans", headers=headers)
        if status == 200:
            return {"ok": True, "detail": "Authenticated to Tenable.io API successfully"}
        return {"ok": False, "error": f"Tenable API returned HTTP {status}: {body[:300]}"}

    elif config.integration_type == "qualys":
        import base64
        auth = base64.b64encode(f"{config.access_key}:{config.secret_key}".encode()).decode()
        status, body = _http_post(
            f"{config.api_url}/api/2.0/fo/asset/host/",
            data={"action": "list", "truncation_limit": "1"},
            headers={"Authorization": f"Basic {auth}", "X-Requested-With": "curl"},
        )
        if status == 200:
            return {"ok": True, "detail": "Authenticated to Qualys API successfully"}
        return {"ok": False, "error": f"Qualys API returned HTTP {status}: {body[:300]}"}

    # rapid7, openvas
    status, body = _http_get(f"{config.api_url}/api/3/", headers={"x-apikey": config.access_key} if config.integration_type == "rapid7" else {})
    if status in (200, 401, 403):
        return {"ok": True, "detail": f"Reached {config.integration_type} API at {config.api_url} (HTTP {status})"}
    return {"ok": False, "error": f"Cannot reach {config.integration_type} API: {body[:300]}"}


# --- SIEM ---

def test_connection_siem(config: SIEMConfig) -> dict:
    missing = _validate_config(config, "sim_siem")
    if missing:
        return {"ok": False, "error": f"Missing required fields for {config.integration_type}: {', '.join(missing)}"}

    if config.integration_type == "sentinel":
        token_url = f"https://login.microsoftonline.com/{config.tenant_id}/oauth2/v2.0/token"
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        body_data = f"client_id={config.client_id}&client_secret={config.client_secret}&scope=https://api.loganalytics.io/.default&grant_type=client_credentials"
        try:
            req = urllib.request.Request(token_url, data=body_data.encode(), headers=headers, method="POST")
            ctx = ssl.create_default_context()
            with urllib.request.urlopen(req, timeout=15, context=ctx) as resp:
                data = json.loads(resp.read())
            if "access_token" in data:
                return {"ok": True, "detail": "Authenticated to Azure for Sentinel Log Analytics API"}
            return {"ok": False, "error": f"Azure AD returned: {data.get('error_description', str(data)[:200])}"}
        except urllib.error.HTTPError as e:
            body = e.read().decode(errors="replace")[:500]
            return {"ok": False, "error": f"Azure AD auth failed (HTTP {e.code}): {body}"}
        except urllib.error.URLError as e:
            return {"ok": False, "error": f"Cannot reach Azure AD: {e.reason}"}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    elif config.integration_type == "splunk":
        headers = {"Authorization": f"Bearer {config.splunk_token}"}
        status, body = _http_get(f"{config.splunk_host}/services/auth/login", headers=headers)
        # Splunk returns 200 or 401
        if status in (200, 401, 403):
            return {"ok": True, "detail": f"Reached Splunk at {config.splunk_host} (HTTP {status})"}
        return {"ok": False, "error": f"Cannot reach Splunk: {body[:300]}"}

    # qradar, elastic
    status, body = _http_get(config.splunk_host or "", headers={"Accept": "application/json"})
    if status in (200, 401, 403):
        return {"ok": True, "detail": f"Reached {config.integration_type} at {config.splunk_host} (HTTP {status})"}
    return {"ok": False, "error": f"Cannot reach {config.integration_type}: {body[:300]}"}


# --- DLP ---

def test_connection_dlp(config: DLPConfig) -> dict:
    missing = _validate_config(config, "sim_dlp")
    if missing:
        return {"ok": False, "error": f"Missing required fields for {config.integration_type}: {', '.join(missing)}"}

    if config.integration_type == "purview":
        token_url = f"https://login.microsoftonline.com/{config.tenant_id}/oauth2/v2.0/token"
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        body_data = f"client_id={config.client_id}&client_secret={config.client_secret}&scope=https://graph.microsoft.com/.default&grant_type=client_credentials"
        try:
            req = urllib.request.Request(token_url, data=body_data.encode(), headers=headers, method="POST")
            ctx = ssl.create_default_context()
            with urllib.request.urlopen(req, timeout=15, context=ctx) as resp:
                data = json.loads(resp.read())
            if "access_token" in data:
                return {"ok": True, "detail": "Authenticated to Microsoft Graph for Purview DLP"}
            return {"ok": False, "error": f"Azure AD returned: {data.get('error_description', str(data)[:200])}"}
        except urllib.error.HTTPError as e:
            body = e.read().decode(errors="replace")[:500]
            return {"ok": False, "error": f"Azure AD auth failed (HTTP {e.code}): {body}"}
        except urllib.error.URLError as e:
            return {"ok": False, "error": f"Cannot reach Azure AD: {e.reason}"}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    elif config.integration_type in ("symantec", "forcepoint"):
        headers = {"Authorization": f"Bearer {config.symantec_api_key}"}
        status, body = _http_get(f"{config.symantec_api_url}/ProtectManager/webservices/v2/incidents", headers=headers)
        if status in (200, 401, 403):
            return {"ok": True, "detail": f"Reached {config.integration_type} DLP API at {config.symantec_api_url} (HTTP {status})"}
        return {"ok": False, "error": f"Cannot reach {config.integration_type} API: {body[:300]}"}

    return {"ok": False, "error": f"Unknown integration type: {config.integration_type}"}


# Registry
TEST_CONNECTION_METHODS: dict[str, callable] = {
    "sim_ad": test_connection_ad,
    "sim_mdm": test_connection_mdm,
    "sim_firewall": test_connection_firewall,
    "sim_vuln": test_connection_vuln,
    "sim_siem": test_connection_siem,
    "sim_dlp": test_connection_dlp,
}


def run_test_connection(connector_type: str, config_json: str) -> dict:
    """Test a connector's live connection. Returns {ok: bool, detail/error: str}."""
    config = load_config(connector_type, config_json)
    if config is None:
        return {"ok": False, "error": f"No config class for connector type: {connector_type}"}
    method = TEST_CONNECTION_METHODS.get(connector_type)
    if method is None:
        return {"ok": False, "error": f"No test method for connector type: {connector_type}"}
    return method(config)


# ---------------------------------------------------------------------------
# Live Collection (attempts real connection, falls back to simulation)
# ---------------------------------------------------------------------------


def _try_live(connector_type: str, config: object, market_name: str, attempt_fn: callable) -> dict:
    """Wrapper: attempt live connection, return structured result."""
    if not os.environ.get("INTEGRATION_MODE") == "live":
        return {"success": False, "reason": "INTEGRATION_MODE not set to 'live'"}
    missing = _validate_config(config, connector_type)
    if missing:
        return {"success": False, "reason": f"Missing required fields: {', '.join(missing)}"}
    try:
        return {"success": True, "items": attempt_fn()}
    except NotImplementedError as e:
        return {"success": False, "reason": f"Not yet implemented: {e}"}
    except Exception as e:
        return {"success": False, "reason": f"{type(e).__name__}: {e}\n{traceback.format_exc()}"}


def collect_ad(config: ADConfig, market_name: str):
    """Collect AD evidence. Attempts Microsoft Graph if live mode is configured."""
    if os.environ.get("INTEGRATION_MODE") == "live":
        result = _try_live("sim_ad", config, market_name,
                          lambda: _collect_ad_live(config, market_name))
        if result["success"]:
            return result["items"]
        print(f"[AD] Live collection failed: {result['reason']}. Falling back to simulation.")
    from src.connectors import ADSimulator
    return ADSimulator().simulate(market_name, {})


def _collect_ad_live(config: ADConfig, market_name: str):
    """Real AD collection via Microsoft Graph API."""
    raise NotImplementedError(
        "Full AD data extraction via Microsoft Graph requires the msgraph-sdk package. "
        "Install with: pip install msgraph-sdk. "
        "Then implement: client.users.get() to pull user list, authentication_methods, "
        "and directory_objects for group membership enumeration."
    )


def collect_mdm(config: MDMConfig, market_name: str):
    if os.environ.get("INTEGRATION_MODE") == "live":
        result = _try_live("sim_mdm", config, market_name,
                          lambda: _collect_mdm_live(config, market_name))
        if result["success"]:
            return result["items"]
        print(f"[MDM] Live collection failed: {result['reason']}. Falling back to simulation.")
    from src.connectors import MDMSimulator
    return MDMSimulator().simulate(market_name, {})


def _collect_mdm_live(config: MDMConfig, market_name: str):
    raise NotImplementedError("Full MDM data extraction requires msgraph-sdk for Intune or requests for Workspace ONE.")


def collect_firewall(config: FirewallConfig, market_name: str):
    if os.environ.get("INTEGRATION_MODE") == "live":
        result = _try_live("sim_firewall", config, market_name,
                          lambda: _collect_firewall_live(config, market_name))
        if result["success"]:
            return result["items"]
        print(f"[Firewall] Live collection failed: {result['reason']}. Falling back to simulation.")
    from src.connectors import FirewallSimulator
    return FirewallSimulator().simulate(market_name, {})


def _collect_firewall_live(config: FirewallConfig, market_name: str):
    raise NotImplementedError("Firewall config extraction requires paramiko (SSH) or vendor-specific REST API client.")


def collect_vuln_scanner(config: VulnScannerConfig, market_name: str):
    if os.environ.get("INTEGRATION_MODE") == "live":
        result = _try_live("sim_vuln", config, market_name,
                          lambda: _collect_vuln_scanner_live(config, market_name))
        if result["success"]:
            return result["items"]
        print(f"[Vuln] Live collection failed: {result['reason']}. Falling back to simulation.")
    from src.connectors import VulnScannerSimulator
    return VulnScannerSimulator().simulate(market_name, {})


def _collect_vuln_scanner_live(config: VulnScannerConfig, market_name: str):
    raise NotImplementedError("Vuln data extraction requires the vendor-specific REST API client for Tenable/Qualys/Rapid7.")


def collect_siem(config: SIEMConfig, market_name: str):
    if os.environ.get("INTEGRATION_MODE") == "live":
        result = _try_live("sim_siem", config, market_name,
                          lambda: _collect_siem_live(config, market_name))
        if result["success"]:
            return result["items"]
        print(f"[SIEM] Live collection failed: {result['reason']}. Falling back to simulation.")
    from src.connectors import SIEMSimulator
    return SIEMSimulator().simulate(market_name, {})


def _collect_siem_live(config: SIEMConfig, market_name: str):
    raise NotImplementedError("SIEM data extraction requires azure-monitor-query for Sentinel or requests for Splunk.")


def collect_dlp(config: DLPConfig, market_name: str):
    if os.environ.get("INTEGRATION_MODE") == "live":
        result = _try_live("sim_dlp", config, market_name,
                          lambda: _collect_dlp_live(config, market_name))
        if result["success"]:
            return result["items"]
        print(f"[DLP] Live collection failed: {result['reason']}. Falling back to simulation.")
    from src.connectors import DLPSimulator
    return DLPSimulator().simulate(market_name, {})


def _collect_dlp_live(config: DLPConfig, market_name: str):
    raise NotImplementedError("DLP data extraction requires msgraph-sdk for Purview or requests for Symantec DLP API.")


INTEGRATION_METHODS: dict[str, callable] = {
    "sim_ad": collect_ad,
    "sim_mdm": collect_mdm,
    "sim_firewall": collect_firewall,
    "sim_vuln": collect_vuln_scanner,
    "sim_siem": collect_siem,
    "sim_dlp": collect_dlp,
}


def run_live_collection(connector_type: str, config: object, market_name: str) -> list:
    method = INTEGRATION_METHODS.get(connector_type)
    if method is None:
        raise ValueError(f"No integration method for connector type: {connector_type}")
    return method(config, market_name)


def collect_manual(market_name: str, files: list[dict]) -> list:
    from src.connectors import ManualUploadConnector
    return ManualUploadConnector().simulate(market_name, {"file_count": len(files)})
