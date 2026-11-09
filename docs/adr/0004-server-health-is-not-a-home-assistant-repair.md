# Represent server health with entities instead of repair issues

Existing decision, recorded 2026-11-07.

The integration exposes Unraid health conditions through entities. Repairs address actionable Home Assistant configuration problems.
Earlier disk, parity, connection, and share-fallback repair issues and stored disk-I/O acknowledgements are
removed during setup. Connection and authentication failures use availability, setup retry, and
reauthentication flows as appropriate. The service-target migration warning asks users to update ambiguous multi-server actions in Home Assistant.

## Consequences

Users can build their own health notifications and automations from entities. Unknown data must remain
distinct from confirmed absence: for example, unavailable array information does not establish that a
server is pool-only or justify hiding its parity support.

## Evidence

- [Legacy repair cleanup and setup failure handling](../../custom_components/unraid_management_agent/__init__.py)
- [Pool-only detection](../../custom_components/unraid_management_agent/coordinator.py)
- [Repair policy](../../AGENTS.md#home-assistant-patterns)
- [Recorded removal](../../CHANGELOG.md)
