# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

## [1.1.0] - 2026-05-12

### Security
- Added `_SensitiveDataFilter` logging filter to redact the API key from all log output, including exception tracebacks
- Logging is now initialised after the API key is loaded so no unfiltered handler is ever active
- Added `--org-id` numeric validation to prevent malformed values from being interpolated into API URLs
- Added CSV formula injection guard (`_sanitize_csv_field`) for `Network Name` and `DeviceName` fields

### Added
- `_fetch_all_pages` generic pagination helper using Meraki Link-header pagination
- Full pagination applied to all endpoints: `networks`, `vpn/statuses`, `internetPolicies`, `appliance/uplink/statuses`, `vpnExclusions/byNetwork`
- 429 rate-limit retry with `Retry-After` backoff in `_build_vpn_uplink_selection_lookup`
- Warning logged when output CSV already exists and will be overwritten
- Log file now written alongside the output CSV (same base name, `.log` extension) instead of hardcoded `appliance_audit.log` in the working directory
- `_fetch_all_data` function to consolidate all API fetch calls out of `main()`
- `requirements.txt` with pinned `httpx>=0.27`
- `.gitignore` to exclude `*.csv` and `*.log` output files
- `LICENSE.md` (MIT)
- README: read-only API key requirement and lab testing recommendation

### Changed
- `_print_rows` renamed to `_write_csv`
- `_validate_api_key_and_org` refactored to use the shared `httpx.Client` instead of a standalone `httpx.get` call
- Single `PER_PAGE = 200` constant replaces separate `INVENTORY_PER_PAGE` and `PAGES_PER_PAGE` constants

## [1.0.0] - 2026-05-12

### Added
- Initial release of `mx_license_audit.py`
- Audits MX appliance licensing levels (Advantage / Essential / Unknown) across a Meraki organization
- CSV report with columns: OrgId, NetworkId, Network Name, DeviceName, deviceSerial, NumberWANLink, VPN, InternetPolicies, VPNUplinkSelection, VPNExclusion, FeatureLevel
- Log file (`appliance_audit.log`) written to the working directory
- API key and organization ID validation before audit begins
- Paginated inventory device fetching
- Per-network uplink selection policy lookup
