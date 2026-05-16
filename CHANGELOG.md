# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added
- Added PEP 723 inline script metadata to `manage_api_key.py` so `uv run manage_api_key.py ...` resolves dependencies automatically.

### Changed
- Updated README examples to use `uv run manage_api_key.py` consistently.
- Simplified Option 2 keyring documentation by removing OS-specific subsections, since `manage_api_key.py` now handles platform differences.

## [2.0.3] - 2026-05-16

### Added
- New `manage_api_key.py` tool for complete API key management with cross-platform support
  - Commands: `set` (store/update), `get` (retrieve for shell export), `read` (display status), `delete` (remove with confirmation)
  - Automatically detects and uses the appropriate keystore: Keychain (macOS), Credential Manager (Windows), Secret Service (Linux)
  - Handles platform-specific setup instructions if keyring backend unavailable
  - Provides masked key display for security

### Removed
- Old `get_api_key.py` script replaced by comprehensive `manage_api_key.py` tool

### Changed
- Updated README with documentation for new `manage_api_key.py` commands and examples
- Quick Start now recommends using `manage_api_key.py set` for consistent cross-platform key setup

## [2.0.2] - 2026-05-16

### Changed
- Enhanced organization validation error message: when an invalid organization ID is provided, the script now displays a formatted table with both Organization ID and Organization Name for easy reference

## [2.0.1] - 2026-05-16

### Added
- Integrated system keyring support for API key storage: script now checks `MERAKI_DASHBOARD_API_KEY` environment variable first, then falls back to system keyring
  - Keychain on macOS, Credential Manager on Windows, Secret Service on Linux
  - Eliminates the need to export API key in every shell session
  - Provides platform-specific instructions if no key is found
  - Added `keyring>=25.0` dependency for cross-platform keyring access
- New `_get_api_key_from_environment_or_keyring()` function centralizes API key resolution

### Changed
- Updated README with clarified configuration instructions for both environment variable and keyring approaches
- Quick Start section now emphasizes storing key in system keyring (one-time setup)

## [2.0.0] - 2026-05-16

### Changed
- **BREAKING**: Migrated from manual `httpx` transport to the official Meraki Python SDK (`meraki>=3.1`) for simplified code maintenance
  - Removed manual HTTP client setup, custom headers, and timeout configuration
  - Removed generic `_fetch_all_pages()` pagination helper; SDK now handles all pagination, retries, and rate-limit backoff automatically
  - Simplified `_validate_api_key_and_org()` and `_fetch_all_data()` to use SDK methods
  - Updated error handling to use SDK exception types (`meraki.APIError`, `meraki.APIKeyError`)
  - Replaced manual retry logic in `_build_vpn_uplink_selection_lookup()` with SDK's built-in retry mechanism
  - Removed `sys`, `time`, and `httpx` imports
- Reduced codebase complexity by ~150 LOC while maintaining identical functionality
- SDK manages authentication, pagination, and retry logic; no manual headers or timeout configuration required
- Added single-purpose `_get_organization_appliance_sdwan_internet_policies()` helper for the one unsupported SDK endpoint (until SDK adds generated support)

### Added
- Documentation in README noting that the script now uses the official Meraki Python SDK

## [1.3.1] - 2026-05-13

### Changed
- Updated README audited feature table to include "Number of Enabled WAN Links" for `NumberWANLinkEnabled`

## [1.3.0] - 2026-05-13

### Added
- CSV output now includes `NumberWANLinkEnabled`, derived from `organizations/{organizationId}/appliance/uplink/statuses`

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
