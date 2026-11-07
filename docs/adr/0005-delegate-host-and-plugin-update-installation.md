# Delegate Unraid OS and plugin installation to Unraid

Existing decision, recorded 2026-11-07.

Unraid OS and plugin update entities report installed and available versions but never offer installation;
users apply those updates in Unraid's web interface. OS updates require a reboot, and the agent's plugin
installation routes were removed following Community Applications review, so exposing a Home Assistant
Install action would advertise an operation the upstream agent deliberately does not provide.
Container-image updates remain installable through the agent when the integration's control settings allow it.

## Consequences

Update availability and install capability are separate concepts. A common update-entity base must not
accidentally grant plugin or OS installation, and read-only mode must retain update visibility while
suppressing installation on otherwise installable container entities.

## Evidence

- [Update-platform contract and entity classes](../../custom_components/unraid_management_agent/update.py)
- [Plugin-update removal and Community Applications rationale](https://github.com/tinkerologie/ha-unraid-management-agent/commit/018fbda)
- [Update behavior recorded in the changelog](../../CHANGELOG.md)
