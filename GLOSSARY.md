# Unraid Management Agent integration

The integration represents Unraid servers and their resources in Home Assistant using the Management Agent.
This vocabulary distinguishes server resources from Home Assistant devices, identities, and health signals.

## Language

### Integration and devices

**Integration**:
The Home Assistant component that monitors and controls configured Unraid servers through the Management Agent.
_Avoid_: Management Agent when referring to the Home Assistant component.

**Management Agent**:
The community Unraid plugin that exposes a server's monitoring data and supported control operations.
_Avoid_: Integration, official Unraid API.

**Configured server**:
One Unraid connection configured in Home Assistant, with its connection settings and integration options.
_Avoid_: Server device when referring to connection configuration.

**Server device**:
The Home Assistant device representing a configured Unraid server as a whole.
_Avoid_: Configured server when referring to the device grouping.

**Group device**:
An optional Home Assistant device grouping a server's Docker or VM Manager entities and resource devices.
_Avoid_: Physical device, individual container, individual VM.

**Resource device**:
A Home Assistant device representing an individual server resource, such as a container, VM, GPU, or pool.
_Avoid_: Separate server, additional configured server.

**Entity**:
One Home Assistant representation of a reading, condition, event, update, or supported control for a configured server.
_Avoid_: Device when referring to an individual reading or control.

**Unique ID**:
The integration's persistent identity for an entity belonging to a particular configured server and resource.
_Avoid_: Entity ID, display name.

**Entity ID**:
The Home Assistant address used to reference an entity in automations and dashboards; it can be renamed.
_Avoid_: Unique ID, resource identifier.

### Collection and availability

**Dynamic mode**:
The collection mode in which the Management Agent chooses collection timing according to demand,
resource policy, and monitoring requirements.
_Avoid_: A Home Assistant polling option.

**Manual mode**:
The collection mode in which enabled collectors run at their configured intervals.
_Avoid_: Disabling WebSocket updates.

**Collector**:
A Management Agent monitoring subsystem responsible for one area of server state, such as disks, containers, or UPS devices.
_Avoid_: Home Assistant entity platform.

**Demand**:
Evidence that a consumer is using a collector's data, through a subscription or a recent read.
_Avoid_: Configured interval, collector enabled state.

**Entity availability**:
Whether a particular entity currently has usable data or a usable control target.
_Avoid_: A healthy reading, confirmed resource absence.

**Server health**:
The operational condition of Unraid and its resources, including disk, parity, temperature, and service problems.
_Avoid_: Home Assistant repair issue.

**Repair issue**:
A Home Assistant issue requiring corrective action within Home Assistant beyond reauthentication or reconfiguration.
_Avoid_: A general Unraid health alert or notification.

**Integration read-only mode**:
The integration option that retains monitoring while suppressing its server control capabilities.
_Avoid_: The Management Agent's MCP read-only mode, server authentication policy.

### Storage and resource readings

**Array**:
Unraid's collection of assigned data disks and any parity disks, distinct from named storage pools.
_Avoid_: Pool, all server storage.

**Pool**:
A named Unraid storage resource separate from the array; a pool may use ZFS or another supported filesystem.
_Avoid_: Array, cache when no particular pool is meant.

**Pool-only server**:
An Unraid server explicitly reporting no array data disks and no parity disks.
_Avoid_: A server whose array data is temporarily unavailable.

**User share**:
A named Unraid view of files stored on its assigned pool or array storage.
_Avoid_: Remote share, storage pool.

**Share content usage**:
The measured space occupied by a user share's contents; an unavailable measurement is different from zero usage.
_Avoid_: Backing storage usage, share capacity.

**Backing storage usage**:
The used, free, and total capacity of the pool or array backing a user share.
Multiple shares on the same storage can report the same backing storage usage.
_Avoid_: Share content usage, per-share quota.

**Exclusive share**:
A user share whose access goes directly to its pool, bypassing Unraid's FUSE user-share layer.
_Avoid_: Private share, access-control setting.

**FUSE fallback**:
The condition in which an exclusive-eligible user share uses the FUSE user-share layer instead of direct pool access.

**Unassigned device**:
A locally attached storage device managed outside the array and named pools through Unassigned Devices.
_Avoid_: Array disk, remote share.

**Remote share**:
A network filesystem mounted on the Unraid server through Unassigned Devices.
_Avoid_: User share, locally attached unassigned device.

**VM guest telemetry**:
Measurements taken inside a configured virtual machine, distinct from the host's view of that VM.

**Update availability**:
The presence of a newer version of a monitored component; availability does not imply that this integration can install it.
_Avoid_: An installable update when the component is display-only.
