"""Prints a shell export statement for MERAKI_DASHBOARD_API_KEY from the OS keystore.

Usage — run via eval so the variable is set in the current shell session:

    macOS / Linux (bash/zsh):
        eval "$(python get_api_key.py)"

    Windows PowerShell:
        Invoke-Expression (python get_api_key.py)

Supported keystores by platform:
  macOS   — Keychain (built-in)
  Windows — Credential Manager (built-in)
  Linux   — Secret Service via GNOME Keyring or KWallet.
            Requires: pip install secretstorage (GNOME) or keyrings.kwallet (KDE).
            On headless systems install keyrings.alt and set PYTHON_KEYRING_BACKEND:
              pip install keyrings.alt
              export PYTHON_KEYRING_BACKEND=keyrings.alt.file.PlaintextKeyring

Service name used: MERAKI_DASHBOARD_API_KEY
"""

import sys
import keyring
import keyring.errors

_KEYSTORE_SERVICE = "MERAKI_DASHBOARD_API_KEY"
_KEYSTORE_USERNAME = "api_key"
_ENV_VAR = "MERAKI_DASHBOARD_API_KEY"

_PLATFORM_HINTS: dict[str, str] = {
    "darwin": (
        "Store the key with:\n"
        "  security add-generic-password -a api_key -s MERAKI_DASHBOARD_API_KEY -w <key>"
    ),
    "win32": (
        "Store the key with:\n"
        "  python -c \"import keyring; keyring.set_password('MERAKI_DASHBOARD_API_KEY', 'api_key', '<key>')\""
    ),
    "linux": (
        "Ensure a Secret Service backend is running (GNOME Keyring or KWallet), then store the key with:\n"
        "  python -c \"import keyring; keyring.set_password('MERAKI_DASHBOARD_API_KEY', 'api_key', '<key>')\"\n"
        "On headless systems: pip install keyrings.alt and set PYTHON_KEYRING_BACKEND=keyrings.alt.file.PlaintextKeyring"
    ),
}


def _export_statement(key: str) -> str:
    """Return the shell-appropriate statement to export the env var."""
    if sys.platform == "win32":
        # PowerShell syntax
        return f"$env:{_ENV_VAR} = '{key}'"
    # bash / zsh / sh
    return f"export {_ENV_VAR}={key}"


def _platform_hint() -> str:
    platform = sys.platform
    return _PLATFORM_HINTS.get(platform, _PLATFORM_HINTS["linux"])


def main() -> None:
    try:
        api_key = keyring.get_password(_KEYSTORE_SERVICE, _KEYSTORE_USERNAME)
    except keyring.errors.NoKeyringError:
        print(
            f"[ERROR] No keyring backend available on this system.\n"
            f"{_platform_hint()}",
            file=sys.stderr,
        )
        raise SystemExit(1)

    if not api_key:
        print(
            f"[ERROR] No API key found in keystore for service '{_KEYSTORE_SERVICE}'.\n"
            f"{_platform_hint()}",
            file=sys.stderr,
        )
        raise SystemExit(1)

    print(_export_statement(api_key))


if __name__ == "__main__":
    main()
