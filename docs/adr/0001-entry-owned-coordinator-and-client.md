# Own monitoring data and connections per configured server

Existing decision, recorded 2026-11-07.

Each configured server owns a coordinator and vendored API client through its config entry's runtime data,
and entity readings come from that coordinator rather than independent polling by every entity.
The client uses Home Assistant's shared HTTP session, while the integration owns its WebSocket lifecycle,
so connection configuration and monitoring state stay scoped to the appropriate server.
Setup completes the first refresh before loading platforms, and successful platform unload is followed by
stopping the WebSocket and closing the client.

## Consequences

New monitoring entities should reuse coordinator data instead of adding their own network reads.
Changing this ownership model would affect setup, unloading, and every entity platform; control actions
can still invoke the client and request a coordinator refresh after a successful operation.

## Evidence

- [Config-entry setup and unload](../../custom_components/unraid_management_agent/__init__.py)
- [Coordinator data ownership](../../custom_components/unraid_management_agent/coordinator.py)
- [Base entity](../../custom_components/unraid_management_agent/entity.py)
- [Vendored client](../../custom_components/unraid_management_agent/api/client.py)
