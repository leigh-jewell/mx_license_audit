# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "keyring>=25.7.0",
#     "meraki>=3.1.0",
# ]
# ///
"""Meraki MX Appliance Configuration Audit

This script uses the Meraki Dashboard API to audit MX appliance configuration to see if they are 
using Advantage license features for a specified organisation. It generates a CSV report with licensing feature indicators
for each appliance. If you have moved to subscription licensing and now have the ability to select
license levels on a per network basis this script can help to understand what networks could have their
license levels lowered based on current feature usage.

Reference:
For a list of features included in each license level, see the Meraki documentation:
https://documentation.meraki.com/Platform_Management/Product_Information/Licensing/Subscription_-_MX_Licensing#Features_Highlights


The following is audited in the MX configuration:
| Feature | API Reference | Description | License Level |
| -------- | -------- | -------- | -------- |
| SD-Internet Steering | InternetPolicies | Controls internet traffic routing based on policies. | Advantage |
| SD-WAN Policies | VPNUplinkSelection | Manages VPN uplink selection for SD-WAN. | Advantage |
| Smart Breakout | VPNExclusion | Allows certain traffic to bypass the VPN. | Advantage |
| VPN Status | VPN Statuses | Indicates if VPN is enabled on the appliance. | Not a license feature but provides context for SD-WAN usage |
| Number of WAN Links | Appliance Uplink Statuses | Shows the number of operational WAN links, which can impact SD-WAN performance benefits. | Not a license feature but provides context for SD-WAN usage |



- Summary Statistics: After CSV output, displayed:
  - Total MX devices audited
  - Count of devices with Advantage licensing
  - Count of devices with Essential licensing
  - Count of devices with Unknown licensing

CSV Columns:
OrgId, NetworkId, Network Name, DeviceName, deviceSerial, NumberWANLink, VPN,
InternetPolicies, VPNUplinkSelection, VPNExclusion, FeatureLevel

FeatureLevel Classification:
- Essential: All three features (InternetPolicies, VPNUplinkSelection, VPNExclusion) are False
- Advantage: Any of the three features are True
- Unknown: Any other combination
"""

import argparse
import csv
import logging
import os
import sys
from typing import Any

import keyring
import keyring.errors
import meraki


PER_PAGE = 200


def _sanitize_log_text(value: Any) -> str:
    """Sanitize untrusted values before writing to logs.

    Replaces CR/LF characters so attackers cannot forge extra log lines.
    """
    return str(value).replace("\r", "\\r").replace("\n", "\\n")


def _get_api_key_from_environment_or_keyring() -> str:
    """Retrieve Meraki API key from environment or system keyring.

    Checks in order:
      1. MERAKI_DASHBOARD_API_KEY environment variable
      2. System keyring (Keychain on macOS, Credential Manager on Windows, Secret Service on Linux)

    Returns:
        str: The API key.

    Raises:
        SystemExit: If no API key found in either location.
    """
    # Try environment variable first
    api_key = os.getenv("MERAKI_DASHBOARD_API_KEY", "").strip()
    if api_key:
        return api_key

    # Try keyring
    try:
        api_key = keyring.get_password("MERAKI_DASHBOARD_API_KEY", "api_key")
    except keyring.errors.NoKeyringError:
        print(
            "[ERROR] No API key found in environment or keyring.\n"
            "To store in keyring:\n"
            "  macOS: security add-generic-password -a api_key -s MERAKI_DASHBOARD_API_KEY -w <key>\n"
            "  Windows: python -c \"import keyring; keyring.set_password('MERAKI_DASHBOARD_API_KEY', 'api_key', '<key>')\"\n"
            "  Linux: python -c \"import keyring; keyring.set_password('MERAKI_DASHBOARD_API_KEY', 'api_key', '<key>')\"",
            file=sys.stderr,
        )
        raise SystemExit(1) from None

    if not api_key:
        print(
            "[ERROR] No API key found in environment or keyring.\n"
            "To store in keyring:\n"
            "  macOS: security add-generic-password -a api_key -s MERAKI_DASHBOARD_API_KEY -w <key>\n"
            "  Windows: python -c \"import keyring; keyring.set_password('MERAKI_DASHBOARD_API_KEY', 'api_key', '<key>')\"\n"
            "  Linux: python -c \"import keyring; keyring.set_password('MERAKI_DASHBOARD_API_KEY', 'api_key', '<key>')\"",
            file=sys.stderr,
        )
        raise SystemExit(1)

    return api_key


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments.

    Returns:
        argparse.Namespace: Parsed arguments containing organization ID and output file.
    """
    parser = argparse.ArgumentParser(
        description=(
            "Report OrgId, NetworkId, Network Name, deviceSerial, VPN, InternetPolicies "
            "for organization appliances."
        ),
    )
    parser.add_argument(
        "-o",
        "--org-id",
        required=True,
        help="Meraki organization ID.",
    )
    parser.add_argument(
        "-f",
        "--file",
        required=True,
        help="Output CSV file path.",
    )
    args = parser.parse_args()
    if not args.org_id.isdigit():
        parser.error("--org-id must be a numeric Meraki organization ID.")
    return args


def _as_list(value: Any) -> list[dict[str, Any]]:
    """Return a list of dictionaries from varied API payload shapes.

    Args:
        value: API response payload.

    Returns:
        list[dict[str, Any]]: Normalized list payload.
    """
    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict)]
    if isinstance(value, dict):
        items = value.get("items")
        if isinstance(items, list):
            return [item for item in items if isinstance(item, dict)]
    return []


def _is_appliance_device(device: dict[str, Any]) -> bool:
    """Return whether an inventory device is an appliance.

    Args:
        device: Inventory device object.

    Returns:
        bool: True when the device appears to be an appliance.
    """
    product_type = str(device.get("productType", "")).strip().lower()
    if product_type:
        return product_type == "appliance"
    model = str(device.get("model", "")).strip().upper()
    return model.startswith("MX") or model.startswith("Z")


def _inventory_rows(inventory_devices: Any) -> list[dict[str, str]]:
    """Build inventory-backed appliance rows.

    Args:
        inventory_devices: Response payload from inventory devices endpoint.

    Returns:
        list[dict[str, str]]: Base rows keyed by serial and network details.
    """
    rows: list[dict[str, str]] = []
    for device in _as_list(inventory_devices):
        if not _is_appliance_device(device):
            continue
        rows.append(
            {
                "network_id": str(device.get("networkId", "")),
                "device_name": str(device.get("name", "")),
                "device_serial": str(device.get("serial", "")),
            }
        )
    return rows


def _vpn_serials(vpn_statuses: Any) -> set[str]:
    """Return serials observed in VPN statuses payload.

    Args:
        vpn_statuses: Response payload from VPN statuses endpoint.

    Returns:
        set[str]: Serials that have VPN status entries.
    """
    serials: set[str] = set()
    for item in _as_list(vpn_statuses):
        serial = str(item.get("deviceSerial", "")).strip()
        if serial:
            serials.add(serial)
    return serials


def _build_policy_lookup(internet_policies: Any) -> dict[str, bool]:
    """Build network-to-policy-presence lookup.

    Args:
        internet_policies: Response payload from internet policies endpoint.

    Returns:
        dict[str, bool]: Mapping of network ID to policy content presence.
    """
    lookup: dict[str, bool] = {}
    for item in _as_list(internet_policies):
        network_id = str(item.get("networkId", "")).strip()
        if not network_id:
            continue
        lookup[network_id] = bool(item.get("wanTrafficUplinkPreferences"))
    return lookup


def _build_network_name_lookup(networks: Any) -> dict[str, str]:
    """Build network ID to network name lookup.

    Args:
        networks: Response payload from organization networks endpoint.

    Returns:
        dict[str, str]: Mapping of network ID to network name.
    """
    lookup: dict[str, str] = {}
    for network in _as_list(networks):
        network_id = str(network.get("id", "")).strip()
        if not network_id:
            continue
        lookup[network_id] = str(network.get("name", "")).strip()
    return lookup


def _get_organization_appliance_sdwan_internet_policies(
    dashboard: meraki.DashboardAPI,
    org_id: str,
) -> list[dict[str, Any]]:
    """Fetch org-wide SD-WAN internet policies through the SDK session.

    The current generated SDK exposes the update operation for this endpoint but
    not the corresponding org-wide GET, so this uses the SDK's own session for
    pagination, retries, and authentication.

    Args:
        dashboard: Configured Meraki SDK client.
        org_id: Organization ID to query.

    Returns:
        list[dict[str, Any]]: Internet policy entries across all pages.
    """
    metadata = {
        "tags": ["appliance", "configure", "sdwan", "internetPolicies"],
        "operation": "getOrganizationApplianceSdwanInternetPolicies",
    }
    return dashboard._session.get_pages(
        metadata,
        f"/organizations/{org_id}/appliance/sdwan/internetPolicies",
        params={"perPage": PER_PAGE},
        total_pages=-1,
    )


def _adaptive_enabled_networks(adaptive_policy_settings: Any) -> set[str]:
    """Return network IDs with Adaptive Policy enabled.

    Args:
        adaptive_policy_settings: Response payload from adaptive policy settings endpoint.

    Returns:
        set[str]: Network IDs with adaptive policy enabled.
    """
    if not isinstance(adaptive_policy_settings, dict):
        return set()
    enabled = adaptive_policy_settings.get("enabledNetworks")
    if not isinstance(enabled, list):
        return set()
    return {str(network_id).strip() for network_id in enabled if str(network_id).strip()}


def _build_vpn_uplink_selection_lookup(
    dashboard: meraki.DashboardAPI,
    rows: list[dict[str, str]],
) -> dict[str, bool]:
    """Build network-to-VPN-uplink-selection lookup.

    Args:
        dashboard: Configured Meraki SDK client.
        rows: Inventory-backed appliance rows.

    Returns:
        dict[str, bool]: Mapping of network ID to VPN uplink selection presence.
    """
    lookup: dict[str, bool] = {}
    network_ids = {row["network_id"] for row in rows if row.get("network_id")}
    logger = logging.getLogger(__name__)

    for network_id in network_ids:
        for attempt in range(3):
            try:
                payload = dashboard.appliance.getNetworkApplianceTrafficShapingUplinkSelection(network_id)
            except meraki.APIError as exc:
                if getattr(exc, "status", None) == 400:
                    lookup[network_id] = False
                    break
                if getattr(exc, "status", None) == 429 and attempt < 2:
                    logger.warning(
                        "Rate limited on network %s, retrying with SDK backoff (attempt %d/3)",
                        _sanitize_log_text(network_id),
                        attempt + 1,
                    )
                    continue
                raise
            lookup[network_id] = (
                bool(payload.get("vpnTrafficUplinkPreferences")) if isinstance(payload, dict) else False
            )
            break

    return lookup


def _sanitize_csv_field(value: str) -> str:
    """Prevent CSV formula injection by prefixing dangerous leading characters.

    Args:
        value: Raw string value destined for a CSV cell.

    Returns:
        str: Safe string value.
    """
    if value and value[0] in ("=", "+", "-", "@", "|", "%"):
        return "'" + value
    return value


def _build_wan_link_count_lookup(appliance_uplink_statuses: Any) -> dict[str, int]:
    """Build network-to-WAN-link-count lookup.

    Args:
        appliance_uplink_statuses: Response payload from appliance uplink statuses endpoint.

    Returns:
        dict[str, int]: Mapping of network ID to number of uplinks.
    """
    lookup: dict[str, int] = {}
    for item in _as_list(appliance_uplink_statuses):
        network_id = str(item.get("networkId", "")).strip()
        if not network_id:
            continue
        uplinks = item.get("uplinks")
        lookup[network_id] = len(uplinks) if isinstance(uplinks, list) else 0
    return lookup


def _is_enabled_uplink(uplink: dict[str, Any]) -> bool:
    """Return whether a WAN uplink should be treated as enabled.

    Meraki payloads can represent enabled state using different fields depending
    on platform/model/firmware. Prefer explicit boolean fields when present and
    fall back to status strings.
    """
    enabled = uplink.get("enabled")
    if isinstance(enabled, bool):
        return enabled

    active = uplink.get("active")
    if isinstance(active, bool):
        return active

    status = str(uplink.get("status", "")).strip().lower()
    if not status:
        return False

    enabled_statuses = {"active", "ready", "connected", "up"}
    disabled_statuses = {
        "not connected",
        "inactive",
        "down",
        "failed",
        "disabled",
        "dormant",
    }
    if status in enabled_statuses:
        return True
    if status in disabled_statuses:
        return False
    return False


def _build_wan_link_enabled_count_lookup(appliance_uplink_statuses: Any) -> dict[str, int]:
    """Build network-to-enabled-WAN-link-count lookup.

    Args:
        appliance_uplink_statuses: Response payload from appliance uplink statuses endpoint.

    Returns:
        dict[str, int]: Mapping of network ID to number of enabled uplinks.
    """
    lookup: dict[str, int] = {}
    for item in _as_list(appliance_uplink_statuses):
        network_id = str(item.get("networkId", "")).strip()
        if not network_id:
            continue
        uplinks = item.get("uplinks")
        if not isinstance(uplinks, list):
            lookup[network_id] = 0
            continue
        lookup[network_id] = sum(
            1 for uplink in uplinks if isinstance(uplink, dict) and _is_enabled_uplink(uplink)
        )
    return lookup


def _build_vpn_exclusion_lookup(vpn_exclusions_by_network: Any) -> dict[str, bool]:
    """Build network-to-VPN-exclusion-presence lookup.

    Args:
        vpn_exclusions_by_network: Response payload from VPN exclusions by network endpoint.

    Returns:
        dict[str, bool]: Mapping of network ID to VPN exclusion presence.
    """
    lookup: dict[str, bool] = {}
    for item in _as_list(vpn_exclusions_by_network):
        network_id = str(item.get("networkId", "")).strip()
        if not network_id:
            continue

        has_custom = isinstance(item.get("custom"), list) and len(item.get("custom", [])) > 0
        has_major = isinstance(item.get("majorApplications"), list) and len(item.get("majorApplications", [])) > 0
        has_applications = isinstance(item.get("applications"), list) and len(item.get("applications", [])) > 0
        lookup[network_id] = has_custom or has_major or has_applications
    return lookup


def _print_summary(counts: dict[str, int]) -> None:
    """Print audit summary statistics to stdout.

    Args:
        counts: Counts of each FeatureLevel and total devices.
    """
    print()
    print(f"Total MX devices audited: {counts['Total']}")
    print(f"Advantage level = {counts['Advantage']}")
    print(f"Essential level = {counts['Essential']}")
    print(f"Unknown level = {counts['Unknown']}")


def _write_csv(
    org_id: str,
    rows: list[dict[str, str]],
    vpn_serials: set[str],
    policy_lookup: dict[str, bool],
    network_name_lookup: dict[str, str],
    vpn_uplink_selection_lookup: dict[str, bool],
    adaptive_enabled_networks: set[str],
    wan_link_count_lookup: dict[str, int],
    wan_link_enabled_count_lookup: dict[str, int],
    vpn_exclusion_lookup: dict[str, bool],
    output_file: str,
) -> dict[str, int]:
    """Write requested columns for each inventory appliance to CSV file.

    Args:
        org_id: Organization ID.
        rows: Inventory-backed appliance rows.
        vpn_serials: Serials with VPN status entries.
        policy_lookup: Network-to-policy-presence mapping.
        network_name_lookup: Network ID to network name mapping.
        vpn_uplink_selection_lookup: Network ID to VPN uplink selection presence mapping.
        adaptive_enabled_networks: Network IDs with adaptive policy enabled.
        wan_link_count_lookup: Network ID to WAN link count mapping.
        wan_link_enabled_count_lookup: Network ID to enabled WAN link count mapping.
        vpn_exclusion_lookup: Network ID to VPN exclusion presence mapping.
        output_file: Path to output CSV file.

    Returns:
        dict[str, int]: Counts of each FeatureLevel and total devices.
    """
    if os.path.exists(output_file):
        logging.getLogger(__name__).warning(
            "Output file %s already exists and will be overwritten.", output_file
        )
    with open(output_file, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "OrgId",
                "NetworkId",
                "Network Name",
                "DeviceName",
                "deviceSerial",
                "NumberWANLink",
                "NumberWANLinkEnabled",
                "VPN",
                "InternetPolicies",
                "VPNUplinkSelection",
                "VPNExclusion",
                "AdaptiveEnabled",
                "FeatureLevel",
            ]
        )

        counts: dict[str, int] = {
            "Total": 0,
            "Advantage": 0,
            "Essential": 0,
            "Unknown": 0,
        }

        for row in rows:
            network_id = row["network_id"]
            device_serial = row["device_serial"]
            network_name = network_name_lookup.get(network_id, "")
            vpn_enabled = device_serial in vpn_serials
            internet_policies_configured = policy_lookup.get(network_id, False)
            vpn_uplink_selection_configured = vpn_uplink_selection_lookup.get(network_id, False)
            adaptive_enabled = network_id in adaptive_enabled_networks
            number_wan_link = wan_link_count_lookup.get(network_id, 0)
            number_wan_link_enabled = wan_link_enabled_count_lookup.get(network_id, 0)
            vpn_exclusion_configured = vpn_exclusion_lookup.get(network_id, False)
            if (
                not internet_policies_configured
                and not vpn_uplink_selection_configured
                and not vpn_exclusion_configured
                and not adaptive_enabled
            ):
                feature_level = "Essential"
            elif (
                internet_policies_configured
                or vpn_uplink_selection_configured
                or vpn_exclusion_configured
                or adaptive_enabled
            ):
                feature_level = "Advantage"
            else:
                feature_level = "Unknown"
            
            counts["Total"] += 1
            counts[feature_level] += 1
            
            writer.writerow(
                [
                    org_id,
                    network_id,
                    _sanitize_csv_field(network_name),
                    _sanitize_csv_field(row["device_name"]),
                    device_serial,
                    number_wan_link,
                    number_wan_link_enabled,
                    vpn_enabled,
                    internet_policies_configured,
                    vpn_uplink_selection_configured,
                    vpn_exclusion_configured,
                    adaptive_enabled,
                    feature_level,
                ]
            )
    
    return counts


def _fetch_all_data(
    dashboard: meraki.DashboardAPI,
    org_id: str,
) -> dict[str, Any]:
    """Fetch all required data from the Meraki API for an organization.

    Args:
        dashboard: Configured Meraki SDK client.
        org_id: Organization ID to audit.

    Returns:
        dict[str, Any]: Mapping of data keys to their fetched payloads.
    """
    logger = logging.getLogger(__name__)
    print("Fetching inventory devices...")
    logger.info("Fetching inventory devices")
    inventory_devices = dashboard.organizations.getOrganizationInventoryDevices(
        org_id,
        total_pages=-1,
        perPage=PER_PAGE,
    )
    appliance_count = len(_inventory_rows(inventory_devices))
    print(f"✓ Found {appliance_count} appliance devices")
    logger.info("Found %d appliance devices", appliance_count)

    print("Fetching networks...")
    networks = dashboard.organizations.getOrganizationNetworks(
        org_id,
        total_pages=-1,
        perPage=PER_PAGE,
    )
    logger.debug("Retrieved %d networks", len(networks))
    print(f"✓ {len(networks)} networks retrieved")

    print("Fetching VPN statuses...")
    vpn_statuses = dashboard.appliance.getOrganizationApplianceVpnStatuses(
        org_id,
        total_pages=-1,
        perPage=PER_PAGE,
    )
    logger.debug("Retrieved %d VPN status entries", len(vpn_statuses))
    print(f"✓ {len(vpn_statuses)} VPN status entries retrieved")

    print("Fetching internet policies...")
    internet_policies = _get_organization_appliance_sdwan_internet_policies(dashboard, org_id)
    logger.debug("Retrieved %d internet policy entries", len(internet_policies))
    print(f"✓ {len(internet_policies)} internet policy entries retrieved")

    print("Fetching appliance uplink statuses...")
    appliance_uplink_statuses = dashboard.appliance.getOrganizationApplianceUplinkStatuses(
        org_id,
        total_pages=-1,
        perPage=PER_PAGE,
    )
    logger.debug("Retrieved %d appliance uplink status entries", len(appliance_uplink_statuses))
    print(f"✓ {len(appliance_uplink_statuses)} appliance uplink status entries retrieved")

    print("Fetching VPN exclusions...")
    vpn_exclusions_by_network = dashboard.appliance.getOrganizationApplianceTrafficShapingVpnExclusionsByNetwork(
        org_id,
        total_pages=-1,
        perPage=PER_PAGE,
    )
    logger.debug("Retrieved %d VPN exclusion entries", len(vpn_exclusions_by_network))
    print(f"✓ {len(vpn_exclusions_by_network)} VPN exclusion entries retrieved")

    print("Fetching Adaptive Policy settings...")
    adaptive_policy_settings = dashboard.organizations.getOrganizationAdaptivePolicySettings(org_id)
    adaptive_enabled_networks = _adaptive_enabled_networks(adaptive_policy_settings)
    logger.debug("Retrieved %d adaptive-enabled networks", len(adaptive_enabled_networks))
    print(f"✓ {len(adaptive_enabled_networks)} adaptive-enabled networks retrieved")

    print("Fetching per-network uplink selection policies...")
    vpn_uplink_selection_lookup = _build_vpn_uplink_selection_lookup(dashboard, _inventory_rows(inventory_devices))
    print("✓ Per-network uplink selections retrieved")
    logger.debug("Per-network uplink selection lookup built successfully")

    return {
        "inventory_devices": inventory_devices,
        "networks": networks,
        "vpn_statuses": vpn_statuses,
        "internet_policies": internet_policies,
        "appliance_uplink_statuses": appliance_uplink_statuses,
        "vpn_exclusions_by_network": vpn_exclusions_by_network,
        "adaptive_enabled_networks": adaptive_enabled_networks,
        "vpn_uplink_selection_lookup": vpn_uplink_selection_lookup,
    }


def _configure_logging(output_file: str, api_key: str) -> None:
    """Configure logging to a file alongside the output CSV.

    A log filter is attached to scrub the API key from all records so it
    is never written to disk.

    Args:
        output_file: Path to the output CSV file used to derive the log file path.
        api_key: Meraki API key to redact from log output.
    """

    class _SensitiveDataFilter(logging.Filter):
        """Redact the API key from log messages and exception tracebacks."""

        def __init__(self, secret: str) -> None:
            super().__init__()
            self._secret = secret

        def filter(self, record: logging.LogRecord) -> bool:
            record.msg = str(record.msg).replace(self._secret, "***REDACTED***")
            if record.exc_text:
                record.exc_text = record.exc_text.replace(self._secret, "***REDACTED***")
            if record.exc_info and record.exc_info[1]:
                exc_str = str(record.exc_info[1])
                if self._secret in exc_str:
                    # Force exc_text to be rendered now so we can scrub it
                    record.exc_text = record.exc_text or ""
            args = record.args
            if isinstance(args, tuple):
                record.args = tuple(
                    str(a).replace(self._secret, "***REDACTED***") if isinstance(a, str) else a
                    for a in args
                )
            elif isinstance(args, dict):
                record.args = {
                    k: str(v).replace(self._secret, "***REDACTED***") if isinstance(v, str) else v
                    for k, v in args.items()
                }
            return True

    base = os.path.splitext(output_file)[0]
    log_file = base + ".log"
    handler = logging.FileHandler(log_file)
    try:
        os.chmod(log_file, 0o600)
    except OSError:
        # Best effort: keep logging even if chmod is not supported.
        pass
    handler.addFilter(_SensitiveDataFilter(api_key))
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[handler],
    )
    logger = logging.getLogger(__name__)
    logger.info("Logging configured. Details written to %s", _sanitize_log_text(log_file))


def _validate_api_key_and_org(dashboard: meraki.DashboardAPI, org_id: str) -> None:
    """Validate API key and confirm organization ID is accessible.

    Args:
        dashboard: Configured Meraki SDK client.
        org_id: Organization ID to verify.

    Raises:
        SystemExit: If API key is invalid or organization ID is not accessible.
    """
    try:
        orgs = dashboard.organizations.getOrganizations(
            total_pages=-1,
            perPage=PER_PAGE,
        )

        org_lookup = {org.get("id"): org.get("name", "N/A") for org in orgs if isinstance(org, dict) and org.get("id")}
        if org_id not in org_lookup:
            print(f"[ERROR] Organization ID '{org_id}' is not available with this API key.")
            print("\nAvailable organizations:")
            print(f"{'Organization ID':<20} {'Organization Name'}")
            print("-" * 60)
            for oid in sorted(org_lookup.keys()):
                print(f"{oid:<20} {org_lookup[oid]}")
            raise SystemExit(1)

    except meraki.APIKeyError as exc:
        print("[ERROR] API key is invalid. Please check your MERAKI_DASHBOARD_API_KEY.")
        raise SystemExit(1) from exc
    except meraki.APIError as exc:
        status = getattr(exc, "status", "unknown")
        message = _sanitize_log_text(exc)
        print(f"[ERROR] Meraki API error status={status}. {message}")
        raise SystemExit(1) from exc
    except Exception as exc:
        print(f"[ERROR] HTTP request failed: {_sanitize_log_text(exc)}")
        raise SystemExit(1) from exc


def main() -> None:
    """Run requests and write appliance audit CSV file."""
    args = parse_args()

    try:
        api_key = _get_api_key_from_environment_or_keyring()

        _configure_logging(args.file, api_key)
        logger = logging.getLogger(__name__)
        logger.info("Starting appliance audit for org %s", args.org_id)
        logger.debug("API key loaded from environment or keyring")

        dashboard = meraki.DashboardAPI(
            api_key=api_key,
            single_request_timeout=30,
            wait_on_rate_limit=True,
            maximum_retries=2,
            output_log=False,
            print_console=False,
            suppress_logging=True,
        )
        logger.info("Validating API key and organization ID")
        _validate_api_key_and_org(dashboard, args.org_id)
        print(f"✓ API key validated, organization {args.org_id} is accessible")

        data = _fetch_all_data(dashboard, args.org_id)

        logger.info("All API calls completed successfully")
        print("Building lookup tables...")
        logger.debug("Parsing API responses and building lookup tables")
        rows = _inventory_rows(data["inventory_devices"])
        vpn_status_serials = _vpn_serials(data["vpn_statuses"])
        policy_lookup = _build_policy_lookup(data["internet_policies"])
        network_name_lookup = _build_network_name_lookup(data["networks"])
        wan_link_count_lookup = _build_wan_link_count_lookup(data["appliance_uplink_statuses"])
        wan_link_enabled_count_lookup = _build_wan_link_enabled_count_lookup(data["appliance_uplink_statuses"])
        vpn_exclusion_lookup = _build_vpn_exclusion_lookup(data["vpn_exclusions_by_network"])
        print("✓ Lookup tables built")
        logger.info("Lookup tables built successfully")

        print(f"Writing results to {args.file}...")
        logger.info("Writing results to CSV file: %s", args.file)
        counts = _write_csv(
            args.org_id,
            rows,
            vpn_status_serials,
            policy_lookup,
            network_name_lookup,
            data["vpn_uplink_selection_lookup"],
            data["adaptive_enabled_networks"],
            wan_link_count_lookup,
            wan_link_enabled_count_lookup,
            vpn_exclusion_lookup,
            args.file,
        )
        _print_summary(counts)
        logger.info("Audit summary: Total=%d, Advantage=%d, Essential=%d, Unknown=%d",
                    counts['Total'], counts['Advantage'], counts['Essential'], counts['Unknown'])
        print(f"✓ Audit complete. Results saved to {args.file}")
        logger.info("Audit completed successfully. Results saved to %s", args.file)
    except meraki.APIKeyError as exc:
        error_msg = f"Invalid Meraki API key. {_sanitize_log_text(exc)}"
        print(f"[ERROR] {error_msg}")
        logger.error(error_msg, exc_info=True)
        raise SystemExit(1) from exc
    except meraki.APIError as exc:
        status = getattr(exc, "status", "unknown")
        error_msg = f"Meraki API error status={status}. {_sanitize_log_text(exc)}"
        print(f"[ERROR] {error_msg}")
        logger.error(error_msg, exc_info=True)
        raise SystemExit(1) from exc
    except Exception as exc:
        error_msg = f"HTTP request failed: {_sanitize_log_text(exc)}"
        print(f"[ERROR] {error_msg}")
        logger.error(error_msg, exc_info=True)
        raise SystemExit(1) from exc
    except (ValueError) as exc:
        error_msg = _sanitize_log_text(exc)
        print(f"[ERROR] {error_msg}")
        logger.error(error_msg, exc_info=True)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
