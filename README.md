# Unraid Management Agent Home Assistant Integration

<!-- BADGES:START -->

[![Marketplace and HACS](https://img.shields.io/badge/Marketplace%20%7C%20HACS-Default-orange.svg)](https://www.hacs.xyz/docs/marketplace/)
[![GitHub Last Commit](https://img.shields.io/github/last-commit/tinkerologie/ha-unraid-management-agent)](https://github.com/tinkerologie/ha-unraid-management-agent/commits/main)
[![GitHub Release](https://img.shields.io/github/v/release/tinkerologie/ha-unraid-management-agent)](https://github.com/tinkerologie/ha-unraid-management-agent/releases)
[![codecov](https://codecov.io/gh/tinkerologie/ha-unraid-management-agent/graph/badge.svg)](https://codecov.io/gh/tinkerologie/ha-unraid-management-agent)
[![License](https://img.shields.io/github/license/tinkerologie/ha-unraid-management-agent)](./LICENSE)

<!-- BADGES:END -->

This integration connects Home Assistant to the [Unraid Management Agent](https://github.com/tinkerologie/unraid-management-agent) on your Unraid server.
Use it to monitor the server, control its resources, and show its data on Home Assistant dashboards.

[Install](#installation) · [Connect a server](#configuration) · [Add dashboard cards](#dashboard-cards) · [Troubleshoot](#troubleshooting)

## Requirements

- Unraid OS 6.9.0 or a subsequent version.
- Home Assistant 2026.11.0 or a subsequent version.
- An active installation of the Unraid Management Agent plugin on Unraid.

Open `http://<unraid-ip>:8043/api/v1/health` in a browser. The response must include `"status": "ok"`.
Use your server address and the agent port.

## Installation

### Install with HACS

[![Open this integration in HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=tinkerologie&repository=ha-unraid-management-agent&category=integration)

Use the button to open the repository in the Home Assistant Community Store (HACS). Use HACS 2.0.1 or a subsequent version.
Select **Download**. Then restart Home Assistant.

If you cannot find the integration, add it as a custom repository. [HACS custom repository instructions](https://www.hacs.xyz/docs/faq/custom_repositories/)

1. Open **HACS** in Home Assistant.
2. Open the three-dot menu.
3. Select **Custom repositories**.
4. Put `https://github.com/tinkerologie/ha-unraid-management-agent` in the repository field.
5. Select **Integration** as the category.
6. Select **Add**.
7. Find **Unraid Management Agent** in HACS.
8. Select **Download**.
9. Restart Home Assistant.

### Install manually

1. Download `unraid_management_agent.zip` from the [latest release](https://github.com/tinkerologie/ha-unraid-management-agent/releases/latest).
2. Make a directory at `<config>/custom_components/unraid_management_agent/`.
3. Extract the ZIP into that directory.
4. Make sure that `manifest.json` is directly in the new directory.
5. Restart Home Assistant.

#### Verify the download

Download `SHA256SUMS` from the same release. Put it in the directory that contains the ZIP.
Replace `RELEASE_TAG` with the release tag. Run these commands from that directory with the [GitHub CLI](https://cli.github.com/) available.

```bash
tag='RELEASE_TAG'
sha256sum -c SHA256SUMS
gh attestation verify unraid_management_agent.zip --repo tinkerologie/ha-unraid-management-agent --signer-workflow tinkerologie/ha-unraid-management-agent/.github/workflows/release.yml
gh release verify-asset "$tag" unraid_management_agent.zip --repo tinkerologie/ha-unraid-management-agent
```

HACS uses the ZIP file with this name. An older release without the ZIP can fail to install.

## Configuration

### Connect a server

Home Assistant can find agents that advertise the Zeroconf service `_unraid-mgmt-agent._tcp.local.`.
For a discovered server, select **Configure** to open its setup form.

For manual setup, do these steps.

1. Open **Settings** > **Devices & Services**.
2. Select **Add Integration**.
3. Find **Unraid Management Agent**.

Complete the setup form.

| Field                                      | Value                                                                                                     |
| ------------------------------------------ | --------------------------------------------------------------------------------------------------------- |
| **Host**                                   | The IP address or hostname of your Unraid server.                                                         |
| **Port**                                   | The agent API port. The default is `8043`.                                                                |
| **API Token**                              | Put the token in this field if the agent uses `API_TOKEN`. Use agent v2026.08.02 or a subsequent version. |
| **Enable WebSocket for real-time updates** | Keep this option on to receive updates from the agent between polls.                                      |

Select **Submit**. The integration sends the token as a bearer token. If you change the token on the agent, use the new token when Home Assistant requests it.

### Integration options

Select **Configure** on the integration entry to change its options.

| Option                                              | Default       | Effect                                                                                                                           |
| --------------------------------------------------- | ------------- | -------------------------------------------------------------------------------------------------------------------------------- |
| **Enable container update checks**                  | Off           | Checks container image digests and adds an update entity for each container.                                                     |
| **Enable fan control entities**                     | On            | Adds number entities for supported pulse-width modulation (PWM) fan controls.                                                    |
| **Enable read-only mode (sensors only)**            | Off           | Disables control entities and actions. Monitoring continues.                                                                     |
| **Enable WebSocket for real-time updates**          | On            | Receives updates through WebSocket. Polling continues if the connection fails.                                                   |
| **Show Docker containers as separate devices**      | Off           | Adds one child device for each container in the Docker device group.                                                             |
| **Show GPUs as separate devices**                   | Off           | Adds one child device for each GPU. The integration uses its UUID or PCI address as its identifier.                              |
| **Show network cards as separate devices**          | Off           | Adds one device for each PCI network card. The agent must run the `nic` collector.                                               |
| **Show USB sensor controllers as separate devices** | Off           | Adds one device for each supported USB sensor controller, with its fan and temperature sensors.                                  |
| **Show virtual machines as separate devices**       | Off           | Adds one child device for each virtual machine (VM). The agent must support `vm_guest_agent` to show sensors from inside the VM. |
| **Show ZFS pools as separate devices**              | Off           | Adds one device for each ZFS pool, with pool sensors and a summary of drive health.                                              |
| **CPU temperature source**                          | **Automatic** | Uses the CPU temperature from the agent. Select a hardware monitor channel to use its reading.                                   |

The form always shows the read-only and WebSocket options. It shows other options when the server reports the related hardware or service.
The form continues to show an enabled option so that you can turn it off. The integration keeps the values of hidden options.
If server data is unavailable, the form shows all options.

If you select a CPU temperature channel, the sensor is unavailable when the agent does not report that channel.

### Agent collection mode

Agent v2026.10.01 and subsequent versions can use Dynamic or Manual collection. Set the mode on the agent.

- **Dynamic**. The agent adjusts each collector interval as demand changes. The integration subscribes to the WebSocket topics it uses. While WebSocket is connected, the 30-second poll skips the data that those topics supply. The integration does a full poll at 10-minute intervals and after each reconnect. If WebSocket is off or disconnected, the full poll runs at 30-second intervals.
- **Manual** or agents without collection modes. The integration receives all events when WebSocket is on. The full poll runs at 30-second intervals.

The **System Status** sensor shows the mode in `collection_mode`.
Diagnostics show the active WebSocket topics and the value of each collector's `effective_interval_seconds` and `reason`.

## Dashboard cards

The integration includes 15 dashboard cards. It registers them during setup.
The cards use devices and entities from this integration.
Use the card picker to find cards with names that start with **Unraid Management Agent**.

### Add the dashboard card

Use the dashboard card to monitor your server in one card. Select a tab to see its data.
The card can select a server automatically. To specify a server, set `server` to its device name or ID.

```yaml
type: custom:unraid-management-agent-dashboard-card
```

This example selects a server and sets the card title. Replace `tower` with your server's device name or ID.

```yaml
type: custom:unraid-management-agent-dashboard-card
server: tower
title: Main Unraid Server
```

### Select an individual card

Use an individual card to show only one set of data or controls.

| Card               | YAML type                                                | Data and controls                                                                 |
| ------------------ | -------------------------------------------------------- | --------------------------------------------------------------------------------- |
| Server             | `custom:unraid-management-agent-server-card`             | CPU, memory, uptime, system load, and array status.                               |
| Storage            | `custom:unraid-management-agent-storage-card`            | Array status, parity checks, cache pools, and drive health.                       |
| Docker             | `custom:unraid-management-agent-docker-card`             | Container status, controls, CPU use, memory use, and updates.                     |
| Virtual machines   | `custom:unraid-management-agent-vm-card`                 | VM status, power controls, CPU allocation, memory allocation, and transfer rates. |
| UPS                | `custom:unraid-management-agent-ups-card`                | Battery charge, load, runtime, voltage, and power.                                |
| GPU                | `custom:unraid-management-agent-gpu-card`                | GPU use, video memory, clock speeds, driver versions, and temperatures.           |
| Network            | `custom:unraid-management-agent-network-card`            | Interface status, IP addresses, link speeds, and transfer rates.                  |
| User shares        | `custom:unraid-management-agent-shares-card`             | Share data size, storage capacity, free space, and parity protection.             |
| Remote shares      | `custom:unraid-management-agent-remote-shares-card`      | SMB and NFS mount state, controls, and capacity.                                  |
| Unassigned devices | `custom:unraid-management-agent-unassigned-devices-card` | External drives, file systems, mount controls, and partitions.                    |
| ZFS                | `custom:unraid-management-agent-zfs-card`                | Pool status, cache hit rate, scrub status, errors, and dataset capacity.          |
| Fans               | `custom:unraid-management-agent-fans-card`               | Fan speed, PWM duty cycle, and speed controls.                                    |
| Notifications      | `custom:unraid-management-agent-notifications-card`      | Alert, warning, and information counts.                                           |
| Maintenance        | `custom:unraid-management-agent-maintenance-card`        | Flash drive health, parity schedule, check history, and sync errors.              |

Each example configures one card.

```yaml
type: custom:unraid-management-agent-server-card
show_system_info: true
```

```yaml
type: custom:unraid-management-agent-docker-card
view_mode: grid
```

### Update older dashboard configurations

1. Back up your dashboard with its raw configuration editor.
2. Change the types of the cards that belong to this integration.
3. Replace `custom:unraid-<module>-card` with `custom:unraid-management-agent-<module>-card`.
4. Select **Save**.
5. Reload the browser page.

For example, use `custom:unraid-management-agent-docker-card` for this integration's Docker card.
The separate Unraid integration uses its own card types.

## Monitoring and controls

The hardware, plugins, and collectors on your server determine which entities are available.

| Area                                 | Data and controls                                                                                                                           |
| ------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------- |
| System                               | CPU and memory use, system load, uptime, boot time, and temperatures.                                                                       |
| Array and parity                     | Array status, capacity, parity progress, schedule, history, and sync errors.                                                                |
| Boot flash drive                     | Drive status, used space, and free space.                                                                                                   |
| Docker                               | Container status, autostart, restart, CPU use, memory use, transfer rates, and image updates.                                               |
| Virtual machines                     | VM status, power, pause, restart, CPU allocation, memory allocation, and transfer rates.                                                    |
| ZFS                                  | Pool status, fragmentation, scrub progress, errors, damaged file paths, and adaptive replacement cache (ARC) data.                          |
| Updates                              | Installed and available versions for Unraid OS and plugins. Install OS and plugin updates in Unraid.                                        |
| Alerts                               | Rule state, severity, firing count, and `firing` and `resolved` events.                                                                     |
| GPUs                                 | GPU use, video memory, temperature, and clock speed.                                                                                        |
| Power                                | Uninterruptible power supply (UPS) charge, load, runtime, and power. Compatible agents report data for each Network UPS Tools (NUT) device. |
| Fans                                 | Speed in revolutions per minute. The integration adds PWM control entities when you enable fan controls.                                    |
| Network                              | Interface status, IP addresses, link speed, maximum transmission unit (MTU), and transfer rates.                                            |
| Services                             | Binary sensors for network and system services, such as SMB, NFS, Docker, and libvirt.                                                      |
| Remote shares and unassigned devices | Mount state, mount switches, and capacity.                                                                                                  |

When container update checks are on, use the container's update entity to install an available image.
Docker and VM entities use the `<server> Docker` and `<server> VMs` devices for data that applies to each service.
Use [integration options](#integration-options) to give individual containers and VMs their own devices.

### User share storage

The **Share {share_name} Storage Usage** sensor reports the capacity of the pool or array that holds the share.
The `storage_used`, `storage_free`, and `storage_total` attributes use `null` for unknown values.
The legacy `total_size` and `free_size` attributes also report storage capacity.

The `used_size` attribute shows how much data the share contains when the agent measures it. The agent can report a value of zero.
The Shares card shows the data size and storage capacity in different fields.

The **FUSE Fallback** problem binary sensor reports when an exclusive share uses FUSE. This sensor is available with agents that report exclusive share state.
Its attributes show the reported locations that prevent exclusive access. Use the sensor in an automation to send a notification.

### SAS storage topology

Use the `storage_topology` collector on the agent. Use `storcli` or `sg3_utils` with SCSI Enclosure Services (SES).
The integration shows controller and enclosure status, temperatures, link speeds, and drive errors.
Compatible agents also report throughput for controllers and enclosures.
Problem sensors report power supply, I/O module, fan, cable, path redundancy, drive, and firmware faults.

## Home Assistant actions

Use actions in automations, scripts, or from **Developer Tools**.
Set **Unraid server** in the action editor, or set `config_entry_id` in YAML.

If you configure one server, you can keep the field empty.
If you configure more than one server, an action without this field uses the first configured server.
Home Assistant creates a Repairs issue for this condition.
Update those automations to specify a server before a future release requires it.

### Docker container actions

- `unraid_management_agent.container_start` — Start a Docker container.
- `unraid_management_agent.container_stop` — Stop a container.
- `unraid_management_agent.container_restart` — Restart a container.
- `unraid_management_agent.container_pause` — Pause a container.
- `unraid_management_agent.container_resume` — Resume a paused container.

```yaml
action: unraid_management_agent.container_restart
data:
  container_id: plex
  config_entry_id: "YOUR_CONFIG_ENTRY_ID"
```

### Virtual machine actions

- `unraid_management_agent.vm_start` — Start a VM.
- `unraid_management_agent.vm_stop` — Shut down a VM.
- `unraid_management_agent.vm_restart` — Restart a VM.
- `unraid_management_agent.vm_pause` — Pause a running VM.
- `unraid_management_agent.vm_resume` — Resume a paused VM.
- `unraid_management_agent.vm_hibernate` — Hibernate a VM.
- `unraid_management_agent.vm_force_stop` — Force a VM to stop.

```yaml
action: unraid_management_agent.vm_start
data:
  vm_id: Ubuntu-Server
```

### Array and parity actions

- `unraid_management_agent.array_start` — Start the storage array.
- `unraid_management_agent.array_stop` — Stop the storage array.
- `unraid_management_agent.parity_check_start` — Start a parity check.
- `unraid_management_agent.parity_check_stop` — Stop a parity check.
- `unraid_management_agent.parity_check_pause` — Pause a parity check.
- `unraid_management_agent.parity_check_resume` — Resume a parity check.

The **Start Array** and **Stop Array** buttons are off by default. To use the buttons, enable them in the entity settings.
If the server has no Unraid array disks, Home Assistant does not create parity entities. Parity actions then give an error.

See the [action reference](custom_components/unraid_management_agent/services.yaml) for the full list and input fields.

## Example automations

Replace the example entity IDs with IDs from your installation.
Replace `notify.mobile_app` with your mobile app's notification action.
For the container action, select the correct server if you have more than one.

### High CPU use alert

```yaml
automation:
  - alias: "Unraid: High CPU Usage Alert"
    trigger:
      - platform: numeric_state
        entity_id: sensor.unraid_tower_cpu_usage
        above: 85
        for:
          minutes: 5
    action:
      - action: notify.mobile_app
        data:
          title: "Unraid Alert: High CPU"
          message: "CPU use is {{ states('sensor.unraid_tower_cpu_usage') }}%. It was above 85% for 5 minutes."
```

### Shutdown when the UPS battery is low

Enable the **Stop Array** button before you use this example.
Use **Stop Array** and **Shutdown System** from the same server.
If you use the `array_stop` action, select the server with `config_entry_id`.

```yaml
automation:
  - alias: "Unraid: UPS Critical Battery Shutdown"
    trigger:
      - platform: numeric_state
        entity_id: sensor.unraid_tower_ups_battery
        below: 15
    action:
      - action: button.press
        target:
          entity_id: button.unraid_tower_stop_array
      - delay:
          seconds: 30
      - action: button.press
        target:
          entity_id: button.unraid_tower_shutdown_system
```

### Send a notification when a rule fires

```yaml
automation:
  - alias: "Unraid: Agent Alert Triggered"
    trigger:
      - platform: state
        entity_id: event.unraid_tower_alert
    condition:
      - condition: template
        value_template: "{{ trigger.to_state.attributes.event_type == 'firing' }}"
    action:
      - action: notify.mobile_app
        data:
          title: "Unraid Alert: {{ trigger.to_state.attributes.severity | upper }}"
          message: "{{ trigger.to_state.attributes.rule_name }}"
```

### Start a container when it stops

```yaml
automation:
  - alias: "Unraid: Restart Vaultwarden on Failure"
    trigger:
      - platform: state
        entity_id: switch.unraid_tower_container_vaultwarden
        to: "off"
        for:
          minutes: 2
    action:
      - action: unraid_management_agent.container_start
        data:
          container_id: vaultwarden
```

## Troubleshooting

### The integration cannot connect

1. Open the agent health URL from [Requirements](#requirements).
2. If the URL does not open, check the agent status and firewall settings on Unraid and your routers.
3. If the agent uses a token, check the token in the **Reconfigure** or reauthentication form.

### Entities are missing

- Check that the related hardware, service, or collector is available on Unraid.
- For SAS devices, check the [SAS storage topology requirements](#sas-storage-topology).
- If you added a container, drive, or pool, reload the integration entry in **Settings** > **Devices & Services**.

### Home Assistant cannot find a dashboard card

1. Make sure that the integration has a configured server.
2. Check the card type against the [card table](#select-an-individual-card).
3. Reload the browser page without the cache.

## Development

The coordinator reads the agent API and receives WebSocket events.
The telemetry package combines the data from these sources for Home Assistant entities.
See the [architecture decisions](docs/adr/README.md) and the [domain glossary](GLOSSARY.md).

Run the commands from the repository root.

```bash
./script/lint
./script/test
./script/develop
```

The first command formats and checks the code. The second runs the tests. The third starts a local Home Assistant instance.
See [Contributing](CONTRIBUTING.md) for setup instructions and contribution requirements.

## License

This project uses the [Apache License 2.0](LICENSE).

## Trademark notice

Unraid is a registered trademark of Lime Technology, Inc.
This community integration operates independently of Lime Technology, Inc. Lime Technology, Inc. does not endorse or sponsor it.
