#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#   "keyring>=25.0",
# ]
# ///

"""Manage Meraki Dashboard API key in OS keystore with cross-platform support.

This tool provides a simple interface to store, retrieve, update, and delete
the MERAKI_DASHBOARD_API_KEY from the system keystore:
  - macOS:   Keychain
  - Windows: Credential Manager
  - Linux:   Secret Service (GNOME Keyring or KWallet)

Usage:
    python manage_api_key.py get                          # Retrieve and export key
    python manage_api_key.py set <your-api-key>          # Store or update key
    python manage_api_key.py delete                       # Remove key from keystore
    python manage_api_key.py read                         # Display key value (masked)

For shell integration (macOS/Linux):
    eval "$(python manage_api_key.py get)"               # Set env var in current session
"""

import argparse
import sys
import keyring
import keyring.errors


_KEYSTORE_SERVICE = "MERAKI_DASHBOARD_API_KEY"
_KEYSTORE_USERNAME = "api_key"
_ENV_VAR = "MERAKI_DASHBOARD_API_KEY"


def _get_platform_name() -> str:
    """Return human-readable platform name."""
    if sys.platform == "darwin":
        return "macOS (Keychain)"
    elif sys.platform == "win32":
        return "Windows (Credential Manager)"
    else:
        return "Linux (Secret Service)"


def _export_statement(key: str) -> str:
    """Return the shell-appropriate statement to export the env var."""
    if sys.platform == "win32":
        # PowerShell syntax
        return f"$env:{_ENV_VAR} = '{key}'"
    # bash / zsh / sh
    return f"export {_ENV_VAR}={key}"


def _mask_key(key: str) -> str:
    """Return a masked version of the API key for display."""
    if len(key) <= 8:
        return "****"
    return key[:4] + "*" * (len(key) - 8) + key[-4:]


def cmd_get(args) -> None:
    """Retrieve API key and print as shell export statement.
    
    This allows piping to eval to set the env var in the current shell session.
    """
    try:
        api_key = keyring.get_password(_KEYSTORE_SERVICE, _KEYSTORE_USERNAME)
    except keyring.errors.NoKeyringError:
        print(
            f"[ERROR] No keyring backend available on {_get_platform_name()}.",
            file=sys.stderr,
        )
        _print_setup_instructions()
        raise SystemExit(1)

    if not api_key:
        print(
            f"[ERROR] No API key found in {_get_platform_name()}.",
            file=sys.stderr,
        )
        _print_setup_instructions()
        raise SystemExit(1)

    print(_export_statement(api_key))


def cmd_set(args) -> None:
    """Store or update API key in the system keystore."""
    if not args.key:
        print("[ERROR] API key is required. Usage: manage_api_key.py set <your-api-key>", file=sys.stderr)
        raise SystemExit(1)

    try:
        keyring.set_password(_KEYSTORE_SERVICE, _KEYSTORE_USERNAME, args.key)
        print(f"✓ API key stored in {_get_platform_name()}")
    except keyring.errors.NoKeyringError:
        print(
            f"[ERROR] No keyring backend available on {_get_platform_name()}.",
            file=sys.stderr,
        )
        _print_setup_instructions()
        raise SystemExit(1)
    except Exception as exc:
        print(f"[ERROR] Failed to store API key: {exc}", file=sys.stderr)
        raise SystemExit(1)


def cmd_read(args) -> None:
    """Display API key status and masked value from the system keystore."""
    try:
        api_key = keyring.get_password(_KEYSTORE_SERVICE, _KEYSTORE_USERNAME)
    except keyring.errors.NoKeyringError:
        print(
            f"[ERROR] No keyring backend available on {_get_platform_name()}.",
            file=sys.stderr,
        )
        _print_setup_instructions()
        raise SystemExit(1)

    if not api_key:
        print(f"[INFO] No API key found in {_get_platform_name()}")
        raise SystemExit(1)

    masked = _mask_key(api_key)
    print(f"✓ API key found in {_get_platform_name()}")
    print(f"  Masked value: {masked}")


def cmd_delete(args) -> None:
    """Delete API key from the system keystore."""
    try:
        api_key = keyring.get_password(_KEYSTORE_SERVICE, _KEYSTORE_USERNAME)
    except keyring.errors.NoKeyringError:
        print(
            f"[ERROR] No keyring backend available on {_get_platform_name()}.",
            file=sys.stderr,
        )
        raise SystemExit(1)

    if not api_key:
        print(f"[INFO] No API key found in {_get_platform_name()} to delete")
        raise SystemExit(0)

    if not args.force:
        confirm = input(f"Delete API key from {_get_platform_name()}? (yes/no): ").strip().lower()
        if confirm not in ("yes", "y"):
            print("Cancelled")
            raise SystemExit(0)

    try:
        keyring.delete_password(_KEYSTORE_SERVICE, _KEYSTORE_USERNAME)
        print(f"✓ API key deleted from {_get_platform_name()}")
    except keyring.errors.PasswordDeleteError:
        print(f"[ERROR] API key not found in {_get_platform_name()}", file=sys.stderr)
        raise SystemExit(1)
    except Exception as exc:
        print(f"[ERROR] Failed to delete API key: {exc}", file=sys.stderr)
        raise SystemExit(1)


def _print_setup_instructions() -> None:
    """Print platform-specific setup instructions for keyring backends."""
    if sys.platform == "darwin":
        print(
            "\nNo setup needed on macOS — Keychain is built-in.\n"
            "Try storing a key: python manage_api_key.py set <your-api-key>",
            file=sys.stderr,
        )
    elif sys.platform == "win32":
        print(
            "\nNo setup needed on Windows — Credential Manager is built-in.\n"
            "Try storing a key: python manage_api_key.py set <your-api-key>",
            file=sys.stderr,
        )
    else:
        print(
            "\nOn Linux, ensure a Secret Service backend is running:\n"
            "  • GNOME: install via your package manager (usually pre-installed)\n"
            "  • KDE: install via your package manager (usually pre-installed)\n"
            "  • Headless: pip install keyrings.alt\n"
            "           export PYTHON_KEYRING_BACKEND=keyrings.alt.file.PlaintextKeyring\n"
            "Then try storing a key: python manage_api_key.py set <your-api-key>",
            file=sys.stderr,
        )


def main() -> None:
    """Parse arguments and dispatch to command handlers."""
    parser = argparse.ArgumentParser(
        description="Manage Meraki Dashboard API key in OS keystore",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python manage_api_key.py get              # Export key for shell use
  eval "$(python manage_api_key.py get)"    # Set env var in current session
  python manage_api_key.py set <key>        # Store new or update key
  python manage_api_key.py read              # Display key status
  python manage_api_key.py delete           # Delete key (with confirmation)
  python manage_api_key.py delete -f        # Delete key (force, no confirm)
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # get command
    subparsers.add_parser(
        "get",
        help="Retrieve API key and print as shell export statement (for use with eval)",
    )

    # set command
    set_parser = subparsers.add_parser("set", help="Store or update API key in keystore")
    set_parser.add_argument("key", nargs="?", help="Meraki Dashboard API key to store")

    # read command
    subparsers.add_parser(
        "read",
        help="Display API key status and masked value",
    )

    # delete command
    delete_parser = subparsers.add_parser("delete", help="Delete API key from keystore")
    delete_parser.add_argument(
        "-f",
        "--force",
        action="store_true",
        help="Delete without confirmation prompt",
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        raise SystemExit(1)

    # Dispatch to command handler
    if args.command == "get":
        cmd_get(args)
    elif args.command == "set":
        cmd_set(args)
    elif args.command == "read":
        cmd_read(args)
    elif args.command == "delete":
        cmd_delete(args)


if __name__ == "__main__":
    main()
