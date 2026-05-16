# MX License Audit

Queries the Meraki Dashboard API to audit MX appliances configuration across an organisation and produces a CSV report classifying each appliance as **Advantage**, **Essential**, or **Unknown** based on active SD-WAN/VPN and Adaptive Policy features enabled. Very helpful for customers that have moved to subscription licensing and want to have different license levels for each network.

The script uses the official Meraki Python SDK for authentication, retries, and pagination.

# Reference:
See the Meraki documentation for a list of features for each each license level. Be aware there are a number of non-configuration features in Advantage. This audit is just for configured features.
https://documentation.meraki.com/Platform_Management/Product_Information/Licensing/Subscription_-_MX_Licensing#Features_Highlights

# Audited:
The following is audited in the MX configuration:
| Feature | API Reference | Description | License Level |
| -------- | -------- | -------- | -------- |
| SD-Internet Steering | InternetPolicies | Controls internet traffic routing based on policies. | Advantage |
| SD-WAN Policies | VPNUplinkSelection | Manages VPN uplink selection for SD-WAN. | Advantage |
| Smart Breakout | VPNExclusion | Allows certain traffic to bypass the VPN. | Advantage |
| Adaptive Policy | adaptivePolicy | Micro-segmentation of traffic according to SGTs | Advantage |
| VPN Status | VPN Statuses | Indicates if VPN is enabled on the appliance. | Not a license feature but provides context for SD-WAN usage |
| Number of WAN Links | Appliance Uplink Statuses | Shows the number of operational WAN links, which can impact SD-WAN performance benefits. | Not a license feature but provides context for SD-WAN usage |
| Number of Enabled WAN Links | Appliance Uplink Statuses | Shows the number of WAN links currently enabled on the appliance. | Not a license feature but provides context for WAN redundancy and utilization |


## Prerequisites

- Python 3.10+
- [`uv`](https://docs.astral.sh/uv/) for environment and dependency management
- A Meraki Dashboard API key with **read-only** access to the target organization

> **Security:** Always use a read-only API key scoped to the minimum required permissions. Never use a full-access or write-enabled key with this script.

> **Testing:** Before running against a production organization, validate the script against a lab or non-production environment to confirm expected behaviour.

## Quick Start

[Install UV](https://docs.astral.sh/uv/getting-started/installation/) for your OS.

If you don't have Python installed then use UV to install it.
```bash
uv python install
```

Store your API key in the system keyring (one-time setup):
```bash
uv run manage_api_key.py set <your-api-key>
```

Run the audit:
```bash
uv run mx_license_audit.py -o <ORG_ID> -f <OUTPUT.csv>
```

## Installation

```bash
uv venv
uv pip sync requirements.lock
```

Windows PowerShell:
```powershell
uv venv
.\.venv\Scripts\Activate.ps1
uv pip sync requirements.lock
```

## Configuration

The script checks for your API key in two locations, in order:

1. **Environment variable** `MERAKI_DASHBOARD_API_KEY` (if set)
2. **System keyring** (Keychain on macOS, Credential Manager on Windows, Secret Service on Linux)

If neither is found, the script exits with instructions on how to store your key.

### Option 1: Environment Variable

```bash
export MERAKI_DASHBOARD_API_KEY=<your-api-key>
uv run mx_license_audit.py -o <ORG_ID> -f <OUTPUT.csv>
```

### Option 2: System Keyring (Recommended)

Store your API key once in the system keyring, and the script will use it automatically:

```bash
uv run manage_api_key.py set <your-api-key>
uv run mx_license_audit.py -o <ORG_ID> -f <OUTPUT.csv>
```

Alternatively, export from keyring to environment:
```bash
eval "$(uv run manage_api_key.py get)"  # Exports the key from keyring to environment
uv run mx_license_audit.py -o <ORG_ID> -f <OUTPUT.csv>
```

> **Security:** Store your API key in the system keyring rather than environment variables. Never paste your key into the command line directly — it will appear in shell history.

## Usage

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
