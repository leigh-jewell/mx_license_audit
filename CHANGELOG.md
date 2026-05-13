# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

## [1.2.0] - 2026-05-13

### Security
- Added log-injection hardening via `_sanitize_log_text` to neutralize CR/LF characters in untrusted values before logging
- Restricted log file permissions to owner-only (`0600`) on supported platforms
- Explicit TLS verification configured on `httpx.Client` (`verify=True`)
- Replaced flat client timeout with explicit phase-specific timeouts (`connect`, `read`, `write`, `pool`)

### Added
- Adaptive Policy support via `GET /organizations/{orgId}/adaptivePolicy/settings`
- New CSV column: `AdaptiveEnabled`
- `get_api_key.py` helper that reads the API key from OS keyring service `MERAKI_DASHBOARD_API_KEY` and emits shell-safe export commands for current-session use
- `requirements.lock` generated with pinned dependency versions (`uv pip compile requirements.txt -o requirements.lock`)

### Changed
- `FeatureLevel` classification now includes Adaptive Policy:
	- `Essential` requires `InternetPolicies`, `VPNUplinkSelection`, `VPNExclusion`, and `AdaptiveEnabled` all `False`
	- `Advantage` is assigned when any of those four flags is `True`
- Simplified data fetching by removing the `_fetch_inventory_devices` wrapper and using `_fetch_all_pages` directly
- Updated README to a `uv`-only workflow for environment, dependency sync, key loading, and script execution
- Updated `.gitignore` to include `.venv/` and common Python cache artifacts

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
