# MX License Audit

Queries the Meraki Dashboard API to audit MX appliance licensing levels across an organization. Produces a CSV report classifying each appliance as **Advantage**, **Essential**, or **Unknown** based on active SD-WAN/VPN features.

## Prerequisites

- Python 3.10+
- [`httpx`](https://www.python-httpx.org/) package
- A Meraki Dashboard API key with read access to the target organization

## Installation

```bash
pip install -r requirements.txt
```

## Configuration

Export your Meraki Dashboard API key as an environment variable before running the script:

```bash
export MERAKI_DASHBOARD_API_KEY="your_api_key_here"
```

## Usage

```bash
python mx_license_audit.py -o <ORG_ID> -f <OUTPUT_FILE.csv>
```

| Argument | Flag | Required | Description |
|---|---|---|---|
| Organization ID | `-o` / `--org-id` | Yes | Meraki organization ID to audit |
| Output file | `-f` / `--file` | Yes | Path for the generated CSV report |

**Example:**

```bash
python mx_license_audit.py -o 123456 -f audit_results.csv
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
| `VPN` | `True` if the appliance has AutoVPN status |
| `InternetPolicies` | `True` if SD-Internet steering policies are configured |
| `VPNUplinkSelection` | `True` if VPN uplink selection preferences are configured |
| `VPNExclusion` | `True` if VPN exclusion (Smart Breakout) rules are configured |
| `FeatureLevel` | `Advantage`, `Essential`, or `Unknown` (see below) |

**FeatureLevel classification:**

- **Essential** — `InternetPolicies`, `VPNUplinkSelection`, and `VPNExclusion` are all `False`
- **Advantage** — any of the three features above is `True`
- **Unknown** — any other combination

### Log File (`appliance_audit.log`)

Written to the current working directory. Contains timestamped debug and info messages covering API calls made, device counts, and any errors encountered during the run.

## License

This project is licensed under the [MIT License](LICENSE.md).
