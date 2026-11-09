# Preserve registry identity while grouping server resources

Existing decision, recorded 2026-11-07.

Entity identities are scoped to a config entry and resource key, with explicit registry migrations when
known legacy key schemes change, rather than rebuilding entities from current display names.
Optional Docker and VM Manager group devices organize child resources beneath the server, with the server
remaining the fallback device when a grouping option is off. This keeps separate servers' resources
distinct and prioritizes existing entity IDs, history, and user customizations over cosmetic normalization.

## Consequences

Resource-key changes require a migration strategy, even when the proposed key looks cleaner.
Grouping and resource-device options are presentation choices within the configured server, not new
server connections; disabling an option can remove entities specific to that option.

Manual resource-device removal and stale-entity cleanup share inventory presence rules.
An inventory the integration can identify as unavailable cannot establish that a resource is absent. Manual removal also requires a successful coordinator update.

## Evidence

- [Entity IDs and device relationships](../../custom_components/unraid_management_agent/entity.py)
- [Legacy migrations and device reparenting](../../custom_components/unraid_management_agent/__init__.py)
- [Registry cleanup](../../custom_components/unraid_management_agent/cleanup.py)
