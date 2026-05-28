#!/usr/bin/env python3
"""
Secure token setup for GitHubGrid.

Uses your system's secret service (KDE Wallet / GNOME Keyring) to store
the token encrypted. Falls back to a plain-text config file only if
secret storage is unavailable.

For the most secure setup, use "gh auth login" instead of this script.
"""
import getpass
import subprocess
import sys

from github_grid.config import set_token, save_config


def _has_secret_tool() -> bool:
    try:
        subprocess.run(
            ["secret-tool", "--version"],
            capture_output=True,
            timeout=5,
        )
        return True
    except Exception:
        return False


def main():
    print("GitHubGrid Secure Token Setup")
    print("=" * 50)
    print()

    has_secret = _has_secret_tool()
    if has_secret:
        print("✓ secret-tool detected — token will be stored in KDE Wallet (encrypted)")
    else:
        print("✗ secret-tool not found — token will be stored in plain-text config")
    print()
    print("Create a token at: https://github.com/settings/tokens")
    print("No scopes required for public contribution data.")
    print()

    token = getpass.getpass("Paste your GitHub token (hidden): ").strip()
    if not token:
        print("No token provided. Exiting.")
        return 1

    username = input("Your GitHub username (optional, leave blank to auto-detect): ").strip() or None
    if username:
        save_config({"username": username})

    stored_securely = set_token(token)

    print()
    if stored_securely:
        print("✓ Token stored securely in KDE Wallet / GNOME Keyring")
    else:
        print("! Token saved to ~/.config/github-grid/config.json (plain text)")
        print("  For better security, install libsecret and run this again.")
    print()
    print("You can now run: ./github-grid")
    return 0


if __name__ == "__main__":
    sys.exit(main())
