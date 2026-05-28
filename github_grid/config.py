import json
import os
import subprocess
from pathlib import Path


CONFIG_DIR = Path.home() / ".config" / "github-grid"
CONFIG_FILE = CONFIG_DIR / "config.json"

# Freedesktop Secret Service attributes for secret-tool
SECRET_LABEL = "GitHubGrid"
SECRET_ATTRS = {"service": "github-grid", "token": "github-token"}


def _secret_tool_lookup() -> str | None:
    """Retrieve token from KDE Wallet / GNOME Keyring via secret-tool."""
    try:
        attrs = " ".join(f"{k} {v}" for k, v in SECRET_ATTRS.items())
        result = subprocess.run(
            ["secret-tool", "lookup"] + attrs.split(),
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            token = result.stdout.strip()
            if token:
                return token
    except FileNotFoundError:
        pass
    except Exception:
        pass
    return None


def _secret_tool_store(token: str) -> bool:
    """Store token in KDE Wallet / GNOME Keyring via secret-tool."""
    try:
        attrs = " ".join(f"{k} {v}" for k, v in SECRET_ATTRS.items())
        proc = subprocess.Popen(
            ["secret-tool", "store", "--label=" + SECRET_LABEL] + attrs.split(),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        stdout, stderr = proc.communicate(input=token, timeout=5)
        return proc.returncode == 0
    except FileNotFoundError:
        return False
    except Exception:
        return False


def _secret_tool_clear() -> bool:
    """Remove token from secret storage."""
    try:
        attrs = " ".join(f"{k} {v}" for k, v in SECRET_ATTRS.items())
        subprocess.run(
            ["secret-tool", "clear"] + attrs.split(),
            capture_output=True,
            timeout=5,
        )
        return True
    except Exception:
        return False


def load_config() -> dict:
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def save_config(config: dict) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)


def get_token() -> str | None:
    """
    Priority:
    1. KWallet / GNOME Keyring via secret-tool (most secure)
    2. GITHUB_TOKEN env var (standard convention)
    3. GITHUB_GRID_TOKEN env var (app-specific)
    4. ~/.config/github-grid/config.json (fallback)
    """
    return (
        _secret_tool_lookup()
        or os.environ.get("GITHUB_TOKEN")
        or os.environ.get("GITHUB_GRID_TOKEN")
        or load_config().get("token")
    )


def set_token(token: str) -> bool:
    """Store token securely. Returns True if stored in KWallet, False if config file."""
    if _secret_tool_store(token):
        return True
    save_config({"token": token})
    CONFIG_FILE.chmod(0o600)
    return False


def clear_token() -> None:
    _secret_tool_clear()
    if CONFIG_FILE.exists():
        CONFIG_FILE.unlink()


def get_username_override() -> str | None:
    return load_config().get("username")
