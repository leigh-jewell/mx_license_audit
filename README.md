# 📊 MX License Audit 📊

> Audits the Meraki MX appliances configuration across an organisation and produces a CSV report classifying each appliance required subscription license level as **Advantage**, **Essential**, or **Unknown** based on active SD-WAN/VPN and Adaptive Policy features enabled.

[![GitHub Release](https://img.shields.io/github/v/release/leigh-jewell/mx_license_audit)](https://github.com/leigh-jewell/mx_license_audit/releases)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE.md)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://python.org/)

---

## 📖 Table of Contents

- [About](#-about)
- [Features](#-features)
- [Prerequisites](#-prerequisites)
- [Quick Start](#-quick-start)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Usage](#-usage)
- [Audited Features](#-audited-features)
- [API Key Management](API_KEY.md)
- [Contributing](#-contributing)
- [License](#-license)

---

## 🧐 About

This tool is perfect for organizations that have migrated to Meraki subscription licensing and can now set the license level for each network rather than the whole orgnisation which was the case for co-term licensing. It automatically analyses your MX appliance configurations and determines the appropriate license tier for each device based on enabled features.

The script uses the official Meraki Python SDK for secure authentication, automatic retries, and pagination. At the moment as Internet Policies API is in BETA it has to be access directly via URL.

**Reference:** See the [Meraki Subscription Licensing Documentation](https://documentation.meraki.com/Platform_Management/Product_Information/Licensing/Subscription_-_MX_Licensing#Features_Highlights) for a complete list of features by license level. Note: This audit only covers *configured* features, not non-configuration features included in Advantage licenses.

---

## ✨ Features

- ⚡ **Fast** — efficient API queries with automatic pagination
- 🔒 **Secure** — uses official Meraki Python SDK with optional keyring storage
- 📋 **Comprehensive** — audits 8+ configuration attributes per device
- 🎯 **Accurate** — classifies devices as Advantage, Essential, or Unknown
- 🌍 **Cross-platform** — works on macOS, Linux, and Windows
- 🛠️ **Minimal dependencies** — only requires Meraki SDK and python-dotenv

---

## 🚀 Prerequisites

- [Python](https://python.org/) >= 3.10
- [`uv`](https://docs.astral.sh/uv/) for environment and dependency management
- A Meraki Dashboard API key with **read-only** access to the target organization

> **Security:** Always use a read-only API key scoped to the minimum required permissions. Never use a full-access or write-enabled key with this script.
>
> **Testing:** Before running against a production organization, validate the script against a lab or non-production environment to confirm expected behaviour.

---

## 🚀 Quick Start

**1. Install UV** (if not already installed):

Official installer (recommended):
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Or using pip:
```bash
pip install uv
```

**2. Install Python** (if needed):
```bash
uv python install
```

**3. Store your API key** (choose one):

Option A - System Keyring (recommended, one-time setup):
```bash
uv run manage_api_key.py set <your-api-key>
```

Option B - Environment Variable:
```bash
export MERAKI_DASHBOARD_API_KEY=<your-api-key>
```

**4. Run the audit:**
```bash
uv run mx_license_audit.py -o <ORG_ID> -f <OUTPUT.csv>
```

---

## 🔧 Installation

```bash
uv venv
uv pip sync requirements.lock
```

**Windows PowerShell:**
```powershell
uv venv
.\.venv\Scripts\Activate.ps1
uv pip sync requirements.lock
```

---

## ⚙️ Configuration

For detailed information on storing and managing your Meraki Dashboard API key, see the [API Key Management Guide](API_KEY.md).

The script checks for your API key in the following locations, **in order**:

1. **Environment variable** `MERAKI_DASHBOARD_API_KEY`
2. **System keyring** (Keychain on macOS, Credential Manager on Windows, Secret Service on Linux)

---

## 💡 Usage

Run the audit with organization ID and output file:

```bash
uv run mx_license_audit.py -o <ORG_ID> -f <OUTPUT.csv>
```

The script will query all MX appliances in the specified organization and produce a detailed CSV report with license classifications.

---

## 📋 Audited Features

The following MX configuration attributes are audited:
| Feature | API Reference | Description | License Level |
| -------- | -------- | -------- | -------- |
| SD-Internet Steering | InternetPolicies | Controls internet traffic routing based on policies. | Advantage |
| SD-WAN Policies | VPNUplinkSelection | Manages VPN uplink selection for SD-WAN. | Advantage |
| Smart Breakout | VPNExclusion | Allows certain traffic to bypass the VPN. | Advantage |
| Adaptive Policy | adaptivePolicy | Micro-segmentation of traffic according to SGTs | Advantage |
| VPN Status | VPN Statuses | Indicates if VPN is enabled on the appliance. | Context |
| Number of WAN Links | Appliance Uplink Statuses | Shows the number of operational WAN links. | Context |
| Number of Enabled WAN Links | Appliance Uplink Statuses | Shows the number of WAN links currently enabled. | Context |

---



```bash
uv run mx_license_audit.py -o <ORG_ID> -f <OUTPUT_FILE.csv>
```

| Argument | Flag | Required | Description |
|---|---|---|---|
| Organization ID | `-o` / `--org-id` | Yes | Meraki organization ID to audit |
| Output file | `-f` / `--file` | Yes | Path for the generated CSV report |

**Example:**

```bash
uv run mx_license_audit.py -o 123456 -f audit_results.csv
```

## API Key Manager

Use `manage_api_key.py` to manage your Meraki Dashboard API key securely in the system keyring.

### Commands

| Command | Description |
|---|---|
| `uv run manage_api_key.py set <key>` | Store or update API key in the system keyring |
| `uv run manage_api_key.py get` | Retrieve API key and print as shell export statement |
| `uv run manage_api_key.py read` | Display API key status and masked value |
| `uv run manage_api_key.py delete` | Delete API key from the system keyring |
| `uv run manage_api_key.py delete -f` | Delete without confirmation prompt |

### Examples

**Store your API key:**
```bash
uv run manage_api_key.py set your-api-key-here
```

**Retrieve and use in current shell session (macOS/Linux):**
```bash
eval "$(uv run manage_api_key.py get)"
uv run mx_license_audit.py -o 123456 -f audit_results.csv
```

**Check key status:**
```bash
uv run manage_api_key.py read
```

**Delete key:**
```bash
uv run manage_api_key.py delete
```

## Output Files

### CSV Report (`<OUTPUT_FILE>`)

Written to the path specified by `-f`. Contains one row per MX appliance with the following columns:

| Column | Description |
|---|---|
| `OrgId` | Meraki organization ID |
| `NetworkId` | Network ID the appliance belongs to |
| `Network Name` | Human-readable network name |
| `DeviceName` | Appliance device name |
| `deviceSerial` | Appliance serial number |
| `NumberWANLink` | Number of active WAN uplinks |
| `NumberWANLinkEnabled` | Number of WAN uplinks currently enabled |
| `VPN` | `True` if the appliance has AutoVPN status |
| `InternetPolicies` | `True` if SD-Internet steering policies are configured |
| `VPNUplinkSelection` | `True` if VPN uplink selection preferences are configured |
| `VPNExclusion` | `True` if VPN exclusion (Smart Breakout) rules are configured |
| `AdaptiveEnabled` | `True` if Adaptive Policy is enabled for the network the MX is in |
| `FeatureLevel` | `Advantage`, `Essential`, or `Unknown` (see below) |

**FeatureLevel classification:**

- **Essential** — `InternetPolicies`, `VPNUplinkSelection`, `VPNExclusion` and `AdaptiveEnabled` are all `False`
- **Advantage** — any of the four features above is `True`
- **Unknown** — any other combination

### Log File (`appliance_audit.log`)

Written alongside the output CSV using the same base name (for example, `audit_results.log` for `audit_results.csv`). Contains timestamped debug and info messages covering API calls made, device counts, and any errors encountered during the run.

## License

This project is licensed under the [MIT License](LICENSE.md).

## Code Guard

Using CodeGuard to ensure security compliance and safety.

https://github.com/cosai-oasis/project-codeguard

## 🤝 Contributing

Contributions are welcome! If you'd like to improve this tool:

1. Fork the project
2. Create your feature branch: `git checkout -b feature/amazing-feature`
3. Commit your changes: `git commit -m 'Add amazing feature'`
4. Push to the branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

---

<p align="center">
  Made with ❤️ by <a href="https://github.com/leigh-jewell">Leigh J</a>
</p>