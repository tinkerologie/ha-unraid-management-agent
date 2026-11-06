# Combine push updates with periodic reconciliation

Existing decision, recorded 2026-11-07.

The integration combines WebSocket updates with periodic REST polling rather than relying exclusively on
either source. In Dynamic mode it subscribes to the topics its enabled resources consume, skips redundant
REST reads for fields covered by the connected filtered stream, and periodically reconciles those fields
and refreshes after reconnects; Manual mode and older agents retain unfiltered updates and regular polling.
WebSocket events notify entity listeners without resetting the coordinator's polling timer, so frequent
events cannot indefinitely postpone reconciliation.

## Consequences

Push updates provide responsiveness while polling repairs missed state. Topic filtering is part of the
Management Agent's demand model, not merely a bandwidth optimization: subscribing to unused topics or
polling every field unnecessarily keeps the corresponding collectors active.

## Evidence

- [Subscription selection and compatibility fallback](../../custom_components/unraid_management_agent/collection.py)
- [Polling, reconnect handling, and event updates](../../custom_components/unraid_management_agent/coordinator.py)
- [Dynamic and Manual behavior](../../README.md#agent-collection-mode)
