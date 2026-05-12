# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

## [1.0.0] - 2026-05-12

### Added
- Initial release of `mx_license_audit.py`
- Audits MX appliance licensing levels (Advantage / Essential / Unknown) across a Meraki organization
- CSV report with columns: OrgId, NetworkId, Network Name, DeviceName, deviceSerial, NumberWANLink, VPN, InternetPolicies, VPNUplinkSelection, VPNExclusion, FeatureLevel
- Log file (`appliance_audit.log`) written to the working directory
- API key and organization ID validation before audit begins
- Paginated inventory device fetching
- Per-network uplink selection policy lookup
