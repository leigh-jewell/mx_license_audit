# 🔑 API Key Management

## Overview

The script checks for your Meraki Dashboard API key in the following locations, **in order**:

1. **Environment variable** `MERAKI_DASHBOARD_API_KEY` (if set)
2. **System keyring** (Keychain on macOS, Credential Manager on Windows, Secret Service on Linux)

If neither is found, the script exits with instructions on how to store your key.

---

## Option 1: Environment Variable

Set your API key as an environment variable:

```bash
export MERAKI_DASHBOARD_API_KEY=<your-api-key>
uv run mx_license_audit.py -o <ORG_ID> -f <OUTPUT.csv>
```

**Pros:**
- Simple and quick
- Suitable for automation and CI/CD pipelines
- Works across all platforms

**Cons:**
- Appears in shell history
- Not persistent across terminal sessions
- Less secure for interactive use

---

## Option 2: System Keyring (Recommended)

Store your API key once in the system keyring for persistent, secure access:

```bash
uv run manage_api_key.py set <your-api-key>
uv run mx_license_audit.py -o <ORG_ID> -f <OUTPUT.csv>
```

**Keyring locations:**
- **macOS**: Keychain
- **Windows**: Credential Manager
- **Linux**: Secret Service

**Pros:**
- Secure storage in OS keyring
- One-time setup
- Doesn't appear in shell history
- Recommended for production use

**Cons:**
- Requires one-time setup
- May require password prompt on first access

### View stored key

To verify your key is stored:

```bash
uv run manage_api_key.py get
```

### Export from keyring to environment

Alternatively, export the key from keyring to environment:

```bash
eval "$(uv run manage_api_key.py get)"  # Exports the key to environment
uv run mx_license_audit.py -o <ORG_ID> -f <OUTPUT.csv>
```

---

## Security Best Practices

> **⚠️ Critical:** Never use a full-access or write-enabled API key with this script. Always use a **read-only** key scoped to the minimum required permissions.

- ✅ Use read-only API keys scoped to your target organization
- ✅ Store keys in the system keyring for production use
- ✅ Never commit API keys to version control
- ✅ Never paste your key into the command line directly — it will appear in shell history
- ❌ Don't hardcode keys in scripts or configuration files
- ❌ Don't use full-access or write-enabled keys

---

## Creating a Meraki Dashboard API Key

1. Log in to [Meraki Dashboard](https://dashboard.meraki.com)
2. Click your account icon in the top right corner
3. Select **My Profile**
4. Scroll to the **API access** section
5. Click **Generate new API key**
6. Copy the key and store it securely using one of the methods above

For more information, see the [Meraki Documentation](https://documentation.meraki.com/General_Administration/Other_Topics/Cisco_Meraki_Dashboard_API).
