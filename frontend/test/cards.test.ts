import { describe, expect, it, vi } from "vitest";
import "../src/index";
import { UnraidServerCard } from "../src/server-card";
import { UnraidStorageCard, formatDiskName } from "../src/storage-card";
import { UnraidSharesCard, formatShareName } from "../src/shares-card";
import { UnraidDockerCard } from "../src/docker-card";
import { UnraidUpsCard, formatRuntime } from "../src/ups-card";
import { UnraidVmCard } from "../src/vm-card";
import { UnraidDashboardCard } from "../src/dashboard-card";
import { UnraidNetworkCard } from "../src/network-card";
import { UnraidZfsCard } from "../src/zfs-card";
import { UnraidFansCard } from "../src/fans-card";
import { UnraidGpuCard } from "../src/gpu-card";
import { UnraidNotificationsCard } from "../src/notifications-card";
import { UnraidMaintenanceCard } from "../src/maintenance-card";
import { UnraidRemoteSharesCard } from "../src/remote-shares-card";
import { UnraidUnassignedDevicesCard } from "../src/unassigned-devices-card";
import {
  UnraidGpuCardEditor,
  UnraidNetworkCardEditor,
  UnraidServerCardEditor,
  UnraidSharesCardEditor,
} from "../src/dashboard-cards-editor";
import type { HomeAssistant } from "../src/ha-types";

function createMockHass(): HomeAssistant {
  const hass: HomeAssistant = {
    states: {
      "sensor.cube_cpu_usage": {
        entity_id: "sensor.cube_cpu_usage",
        state: "15",
        attributes: {
          friendly_name: "CUBE CPU Usage",
          cpu_model: "Intel i7-8700K",
          cpu_cores: 6,
          cpu_threads: 12,
        },
        last_changed: "",
        last_updated: "",
      },
      "sensor.cube_ram_usage": {
        entity_id: "sensor.cube_ram_usage",
        state: "25",
        attributes: {
          friendly_name: "CUBE RAM Usage",
          used: "8 GiB",
          total: "32 GiB",
        },
        last_changed: "",
        last_updated: "",
      },
      "sensor.cube_array_usage": {
        entity_id: "sensor.cube_array_usage",
        state: "10",
        attributes: {
          friendly_name: "CUBE Array Usage",
          capacity_used: "4 TB",
          capacity_total: "40 TB",
          capacity_free: "36 TB",
        },
        last_changed: "",
        last_updated: "",
      },
      "sensor.cube_array_state": {
        entity_id: "sensor.cube_array_state",
        state: "Started",
        attributes: {},
        last_changed: "",
        last_updated: "",
      },
      "binary_sensor.cube_parity_valid": {
        entity_id: "binary_sensor.cube_parity_valid",
        state: "off",
        attributes: { friendly_name: "Cube Parity Valid" },
        last_changed: "",
        last_updated: "",
      },
      "binary_sensor.cube_parity_check_running": {
        entity_id: "binary_sensor.cube_parity_check_running",
        state: "off",
        attributes: { friendly_name: "Cube Parity Check Running", status: "completed" },
        last_changed: "",
        last_updated: "",
      },
      "binary_sensor.cube_parity_status": {
        entity_id: "binary_sensor.cube_parity_status",
        state: "off",
        attributes: { status: "completed" },
        last_changed: "",
        last_updated: "",
      },
      "sensor.cube_disk_disk1_usage": {
        entity_id: "sensor.cube_disk_disk1_usage",
        state: "12",
        attributes: {
          friendly_name: "Cube Disk disk1 usage",
          status: "DISK_OK",
          num_errors: 0,
          spin_state: "active",
        },
        last_changed: "",
        last_updated: "",
      },
      "binary_sensor.cube_disk_disk1_health": {
        entity_id: "binary_sensor.cube_disk_disk1_health",
        state: "off",
        attributes: { status: "DISK_OK" },
        last_changed: "",
        last_updated: "",
      },
      "sensor.cube_disk_disk1_temperature": {
        entity_id: "sensor.cube_disk_disk1_temperature",
        state: "32",
        attributes: {},
        last_changed: "",
        last_updated: "",
      },
      "switch.cube_disk_disk1_spin": {
        entity_id: "switch.cube_disk_disk1_spin",
        state: "on",
        attributes: {},
        last_changed: "",
        last_updated: "",
      },
      "sensor.cube_share_appdata_usage": {
        entity_id: "sensor.cube_share_appdata_usage",
        state: "9.7",
        attributes: {
          friendly_name: "Cube Share appdata usage",
          used: "46.6 GB",
          total: "480.6 GB",
          free: "434.0 GB",
          color: "yellow-on",
        },
        last_changed: "",
        last_updated: "",
      },
      "sensor.cube_share_media_usage": {
        entity_id: "sensor.cube_share_media_usage",
        state: "45.0",
        attributes: {
          friendly_name: "Cube Share media usage",
          used: "18.0 TB",
          total: "40.0 TB",
          free: "22.0 TB",
          color: "green-on",
        },
        last_changed: "",
        last_updated: "",
      },
      "switch.cube_docker_container_plex": {
        entity_id: "switch.cube_docker_container_plex",
        state: "on",
        attributes: { friendly_name: "plex" },
        last_changed: "",
        last_updated: "",
      },
      "sensor.cube_ups_battery": {
        entity_id: "sensor.cube_ups_battery",
        state: "100",
        attributes: {},
        last_changed: "",
        last_updated: "",
      },
      "sensor.cube_ups_load": {
        entity_id: "sensor.cube_ups_load",
        state: "15",
        attributes: {},
        last_changed: "",
        last_updated: "",
      },
      "switch.cube_virtual_machine_ha": {
        entity_id: "switch.cube_virtual_machine_ha",
        state: "on",
        attributes: { friendly_name: "Home Assistant" },
        last_changed: "",
        last_updated: "",
      },
      "sensor.cube_disk_flash_usage": {
        entity_id: "sensor.cube_disk_flash_usage",
        state: "8",
        attributes: {
          friendly_name: "Cube Disk flash usage",
          status: "DISK_OK",
          num_errors: 0,
          device: "sdb",
          fs_size: "31.4 GB",
          fs_used: "2.68 GB",
          fs_free: "28.7 GB",
        },
        last_changed: "",
        last_updated: "",
      },
      "binary_sensor.cube_disk_flash_health": {
        entity_id: "binary_sensor.cube_disk_flash_health",
        state: "off",
        attributes: { status: "DISK_OK" },
        last_changed: "",
        last_updated: "",
      },
      "sensor.cube_network_eth0_ip_address": {
        entity_id: "sensor.cube_network_eth0_ip_address",
        state: "192.168.20.21",
        attributes: {
          friendly_name: "Cube Network eth0 IP",
          mac_address: "00:11:22:33:44:55",
          mtu: 1500,
        },
        last_changed: "",
        last_updated: "",
      },
      "sensor.cube_network_eth0_speed": {
        entity_id: "sensor.cube_network_eth0_speed",
        state: "1000",
        attributes: { unit_of_measurement: "Mbps" },
        last_changed: "",
        last_updated: "",
      },
      "sensor.cube_network_eth0_rx_throughput": {
        entity_id: "sensor.cube_network_eth0_rx_throughput",
        state: "12.4",
        attributes: { total_received: "1.2 GB" },
        last_changed: "",
        last_updated: "",
      },
      "sensor.cube_network_eth0_tx_throughput": {
        entity_id: "sensor.cube_network_eth0_tx_throughput",
        state: "5.8",
        attributes: { total_sent: "650 MB" },
        last_changed: "",
        last_updated: "",
      },
      "binary_sensor.cube_network_eth0_link": {
        entity_id: "binary_sensor.cube_network_eth0_link",
        state: "on",
        attributes: {},
        last_changed: "",
        last_updated: "",
      },
      "sensor.cube_network_access": {
        entity_id: "sensor.cube_network_access",
        state: "http://192.168.20.21",
        attributes: {
          LAN_IPv4_ipv4: "http://192.168.20.21",
          FQDN_LAN_ipv4: "https://cube.myunraid.net",
        },
        last_changed: "",
        last_updated: "",
      },
      "sensor.cube_zfs_arc_hit_ratio": {
        entity_id: "sensor.cube_zfs_arc_hit_ratio",
        state: "95",
        attributes: { unit_of_measurement: "%" },
        last_changed: "",
        last_updated: "",
      },
      "sensor.cube_zfs_tank_usage": {
        entity_id: "sensor.cube_zfs_tank_usage",
        state: "42",
        attributes: {
          pool_name: "tank",
          total_size: "10 TB",
          used_size: "4.2 TB",
          free_space: "5.8 TB",
        },
        last_changed: "",
        last_updated: "",
      },
      "sensor.cube_zfs_tank_health": {
        entity_id: "sensor.cube_zfs_tank_health",
        state: "ONLINE",
        attributes: { pool_name: "tank", errors: 0 },
        last_changed: "",
        last_updated: "",
      },
      "sensor.cube_fan_1": {
        entity_id: "sensor.cube_fan_1",
        state: "1200",
        attributes: {
          friendly_name: "Fan 1 Speed",
          unit_of_measurement: "RPM",
          fan_id: 1,
        },
        last_changed: "",
        last_updated: "",
      },
      "sensor.cube_gpu_0_utilization": {
        entity_id: "sensor.cube_gpu_0_utilization",
        state: "45",
        attributes: {
          gpu_name: "NVIDIA RTX 3080",
          driver_version: "535.129.03",
        },
        last_changed: "",
        last_updated: "",
      },
      "sensor.cube_gpu_0_temperature": {
        entity_id: "sensor.cube_gpu_0_temperature",
        state: "55",
        attributes: {},
        last_changed: "",
        last_updated: "",
      },
      "sensor.cube_notifications_unread_alert": {
        entity_id: "sensor.cube_notifications_unread_alert",
        state: "0",
        attributes: {},
        last_changed: "",
        last_updated: "",
      },
      "sensor.cube_notifications_unread_warning": {
        entity_id: "sensor.cube_notifications_unread_warning",
        state: "1",
        attributes: {},
        last_changed: "",
        last_updated: "",
      },
      "sensor.cube_notifications_unread_info": {
        entity_id: "sensor.cube_notifications_unread_info",
        state: "2",
        attributes: {},
        last_changed: "",
        last_updated: "",
      },
      "sensor.cube_flash_usage": {
        entity_id: "sensor.cube_flash_usage",
        state: "15",
        attributes: {},
        last_changed: "",
        last_updated: "",
      },
      "sensor.cube_last_parity_check": {
        entity_id: "sensor.cube_last_parity_check",
        state: "Completed",
        attributes: { result: "Completed", errors: 0, duration: "8h 12m" },
        last_changed: "",
        last_updated: "",
      },
      "sensor.cube_remote_share_backup_usage": {
        entity_id: "sensor.cube_remote_share_backup_usage",
        state: "35",
        attributes: { friendly_name: "Remote Share backup usage", used: "350 GB", total: "1 TB" },
        last_changed: "",
        last_updated: "",
      },
      "binary_sensor.cube_remote_share_backup_mounted": {
        entity_id: "binary_sensor.cube_remote_share_backup_mounted",
        state: "on",
        attributes: {},
        last_changed: "",
        last_updated: "",
      },
      "sensor.cube_unassigned_device_dev1_size": {
        entity_id: "sensor.cube_unassigned_device_dev1_size",
        state: "2",
        attributes: { friendly_name: "Unassigned Device dev1 size", unit_of_measurement: "TB", filesystem: "exfat" },
        last_changed: "",
        last_updated: "",
      },
      "binary_sensor.cube_unassigned_device_dev1_mounted": {
        entity_id: "binary_sensor.cube_unassigned_device_dev1_mounted",
        state: "on",
        attributes: {},
        last_changed: "",
        last_updated: "",
      },
    },
    devices: {
      dev_1: {
        id: "dev_1",
        name: "CUBE",
        identifiers: [
          ["unraid_management_agent", "uuid-1234"],
          ["unraid", "uuid-1234"],
        ],
        model: "Fractal Node 304",
        sw_version: "6.12.10",
      },
    },
    entities: {},
    callService: async () => Promise.resolve(),
  };
  hass.entities = Object.fromEntries(Object.keys(hass.states).map((entity_id) => [entity_id, {
    entity_id, device_id: "dev_1", platform: "unraid_management_agent",
  }]));
  return hass;
}

// Existing rendering cases add telemetry after creating the fixture. Supply the
// registry evidence that a real Agent entity has, without replacing explicit
// ownership/device relationships in each case.
function withMockRegistry(hass: HomeAssistant): HomeAssistant {
  hass.entities ??= {};
  for (const entity_id of Object.keys(hass.states)) {
    hass.entities[entity_id] ??= { entity_id, device_id: "dev_1", platform: "unraid_management_agent" };
  }
  return hass;
}

describe("Unraid Custom Cards", () => {
  it("registers all cards in window.customCards", () => {
    expect(window.customCards).toBeDefined();
    const tags = window.customCards?.map((c) => c.type);
    expect(tags).toContain("unraid-management-agent-server-card");
    expect(tags).toContain("unraid-management-agent-storage-card");
    expect(tags).toContain("unraid-management-agent-shares-card");
    expect(tags).toContain("unraid-management-agent-docker-card");
    expect(tags).toContain("unraid-management-agent-ups-card");
    expect(tags).toContain("unraid-management-agent-vm-card");
    expect(tags).toContain("unraid-management-agent-network-card");
    expect(tags).toContain("unraid-management-agent-zfs-card");
    expect(tags).toContain("unraid-management-agent-fans-card");
    expect(tags).toContain("unraid-management-agent-gpu-card");
    expect(tags).toContain("unraid-management-agent-notifications-card");
    expect(tags).toContain("unraid-management-agent-maintenance-card");
    expect(tags).toContain("unraid-management-agent-remote-shares-card");
    expect(tags).toContain("unraid-management-agent-unassigned-devices-card");
    expect(tags).toContain("unraid-management-agent-dashboard-card");
  });

  it("formats disk and share names cleanly", () => {
    expect(formatDiskName("Cube Disk disk1 usage", "disk1")).toBe("Disk 1");
    expect(formatDiskName("Tower Disk cache usage", "cache")).toBe("Cache");
    expect(formatDiskName("Cube Disk parity health", "parity")).toBe("Parity");
    expect(formatDiskName("Cube Disk flash usage", "flash")).toBe("Flash (Boot)");
    expect(formatDiskName("disk_2", "disk_2")).toBe("Disk 2");

    expect(formatShareName("Cube Share appdata usage", "appdata")).toBe("appdata");
    expect(formatShareName("Media Share", "media")).toBe("Media");
  });

  it("renders UnraidServerCard with mock hass data and formats numeric uptime", async () => {
    const card = new UnraidServerCard();
    card.setConfig({ type: "custom:unraid-management-agent-server-card" });
    const hass = createMockHass();
    hass.states["sensor.cube_uptime"] = {
      entity_id: "sensor.cube_uptime",
      state: "90000",
      attributes: {},
      last_changed: "",
      last_updated: "",
    };
    card.hass = withMockRegistry(hass);
    document.body.appendChild(card);
    await card.updateComplete;

    expect(card.getCardSize()).toBe(4);
    expect(card.getGridOptions()).toEqual({ columns: 12, min_columns: 6 });
    expect(card.shadowRoot?.innerHTML).toContain("CUBE");
    expect(card.shadowRoot?.innerHTML).toContain("CPU Load");
    expect(card.shadowRoot?.innerHTML).toContain("15%");
    expect(card.shadowRoot?.innerHTML).toContain("1d 1h");
    expect(card.shadowRoot?.innerHTML).toContain("192.168.20.21");
    expect(card.shadowRoot?.innerHTML).toContain("Boot Device");
    expect(card.shadowRoot?.innerHTML).toContain("Flash");
    document.body.removeChild(card);
  });

  it("dispatches hass-more-info event when clicking server rings and supports navigation", async () => {
    const card = new UnraidServerCard();
    card.setConfig({ type: "custom:unraid-management-agent-server-card" });
    card.hass = createMockHass();
    document.body.appendChild(card);
    await card.updateComplete;

    let moreInfoEvent: CustomEvent | null = null;
    card.addEventListener("hass-more-info", ((e: CustomEvent) => {
      moreInfoEvent = e;
    }) as EventListener);

    const cpuRing = card.shadowRoot?.querySelector(".ring-card") as HTMLElement;
    expect(cpuRing).not.toBeNull();
    cpuRing.click();

    expect(moreInfoEvent).not.toBeNull();
    expect((moreInfoEvent as any)?.detail?.entityId).toBe("sensor.cube_cpu_usage");

    // Test navigate helper on BaseUnraidCard
    let locationChanged = false;
    const locHandler = () => {
      locationChanged = true;
    };
    window.addEventListener("location-changed", locHandler);
    (card as any).navigate("/dashboard-unraid/storage");
    expect(locationChanged).toBe(true);
    window.removeEventListener("location-changed", locHandler);

    document.body.removeChild(card);
  });

  it("renders UnraidStorageCard with clean disk names and Healthy badge", async () => {
    const card = new UnraidStorageCard();
    card.setConfig({ type: "custom:unraid-management-agent-storage-card" });
    card.hass = createMockHass();
    document.body.appendChild(card);
    await card.updateComplete;

    expect(card.shadowRoot?.innerHTML).toContain("Storage Array &amp; Disks");
    expect(card.shadowRoot?.innerHTML).toContain("Disk 1");
    expect(card.shadowRoot?.innerHTML).toContain("Flash (Boot)");
    expect(card.shadowRoot?.innerHTML).toContain("Healthy");
    expect(card.shadowRoot?.innerHTML).toContain("Active");
    expect(card.shadowRoot?.innerHTML).toContain("32°C");
    expect(card.shadowRoot?.innerHTML).toContain("Parity Valid");
    expect(card.shadowRoot?.innerHTML).toContain("Parity Status: Valid");
    document.body.removeChild(card);
  });

  it("renders UnraidStorageCard with Parity Valid when progress is 100 and check is not running", async () => {
    const card = new UnraidStorageCard();
    card.setConfig({ type: "custom:unraid-management-agent-storage-card" });
    const mockHass = createMockHass();
    mockHass.states["sensor.cube_parity_progress"] = {
      entity_id: "sensor.cube_parity_progress",
      state: "100",
      attributes: {},
      last_changed: "",
      last_updated: "",
    };
    mockHass.states["switch.cube_parity_check"] = {
      entity_id: "switch.cube_parity_check",
      state: "off",
      attributes: {},
      last_changed: "",
      last_updated: "",
    };
    card.hass = withMockRegistry(mockHass);
    document.body.appendChild(card);
    await card.updateComplete;

    expect(card.shadowRoot?.innerHTML).toContain("Parity Valid");
    expect(card.shadowRoot?.innerHTML).toContain("Parity Status: Valid");
    expect(card.shadowRoot?.innerHTML).not.toContain("Parity Check In Progress");
    expect(card.shadowRoot?.innerHTML).not.toContain("Parity Check Needed");
    expect(card.shadowRoot?.innerHTML).toContain("Check Now");
    document.body.removeChild(card);
  });

  it("renders UnraidStorageCard with Parity Check Needed when validity sensor is on", async () => {
    const card = new UnraidStorageCard();
    card.setConfig({ type: "custom:unraid-management-agent-storage-card" });
    const mockHass = createMockHass();
    mockHass.states["binary_sensor.cube_parity_valid"] = {
      entity_id: "binary_sensor.cube_parity_valid",
      state: "on",
      attributes: { friendly_name: "Cube Parity Valid" },
      last_changed: "",
      last_updated: "",
    };
    mockHass.states["sensor.cube_last_parity_check_errors"] = {
      entity_id: "sensor.cube_last_parity_check_errors",
      state: "5",
      attributes: {},
      last_changed: "",
      last_updated: "",
    };
    card.hass = withMockRegistry(mockHass);
    document.body.appendChild(card);
    await card.updateComplete;

    expect(card.shadowRoot?.innerHTML).toContain("Parity Check Needed");
    expect(card.shadowRoot?.innerHTML).toContain("Parity Status: Check Needed");
    expect(card.shadowRoot?.innerHTML).toContain("5 errors");
    document.body.removeChild(card);
  });

  it("renders UnraidStorageCard with check in progress at 0% and Cancel button", async () => {
    const card = new UnraidStorageCard();
    card.setConfig({ type: "custom:unraid-management-agent-storage-card" });
    const mockHass = createMockHass();
    mockHass.states["binary_sensor.cube_parity_check_running"] = {
      entity_id: "binary_sensor.cube_parity_check_running",
      state: "on",
      attributes: { friendly_name: "Cube Parity Check Running", status: "running" },
      last_changed: "",
      last_updated: "",
    };
    mockHass.states["sensor.cube_parity_progress"] = {
      entity_id: "sensor.cube_parity_progress",
      state: "0",
      attributes: {},
      last_changed: "",
      last_updated: "",
    };
    mockHass.states["switch.cube_parity_check"] = {
      entity_id: "switch.cube_parity_check",
      state: "on",
      attributes: {},
      last_changed: "",
      last_updated: "",
    };
    card.hass = withMockRegistry(mockHass);
    document.body.appendChild(card);
    await card.updateComplete;

    expect(card.shadowRoot?.innerHTML).toContain("Parity Check In Progress (0%)");
    expect(card.shadowRoot?.innerHTML).toContain("Cancel");
    document.body.removeChild(card);
  });

  it("renders UnraidStorageCard with Parity Check Paused", async () => {
    const card = new UnraidStorageCard();
    card.setConfig({ type: "custom:unraid-management-agent-storage-card" });
    const mockHass = createMockHass();
    mockHass.states["binary_sensor.cube_parity_check_running"] = {
      entity_id: "binary_sensor.cube_parity_check_running",
      state: "on",
      attributes: { friendly_name: "Cube Parity Check Running", status: "paused" },
      last_changed: "",
      last_updated: "",
    };
    mockHass.states["sensor.cube_parity_progress"] = {
      entity_id: "sensor.cube_parity_progress",
      state: "42",
      attributes: {},
      last_changed: "",
      last_updated: "",
    };
    card.hass = withMockRegistry(mockHass);
    document.body.appendChild(card);
    await card.updateComplete;

    expect(card.shadowRoot?.innerHTML).toContain("Parity Check Paused (42%)");
    document.body.removeChild(card);
  });

  it("renders UnraidStorageCard with Parity Status Unknown when validity is unknown or unavailable", async () => {
    const card = new UnraidStorageCard();
    card.setConfig({ type: "custom:unraid-management-agent-storage-card" });
    const mockHass = createMockHass();
    mockHass.states["binary_sensor.cube_parity_valid"] = {
      entity_id: "binary_sensor.cube_parity_valid",
      state: "unknown",
      attributes: {},
      last_changed: "",
      last_updated: "",
    };
    delete mockHass.states["binary_sensor.cube_parity_status"];
    card.hass = withMockRegistry(mockHass);
    document.body.appendChild(card);
    await card.updateComplete;

    expect(card.shadowRoot?.innerHTML).toContain("Parity Status Unknown");
    expect(card.shadowRoot?.innerHTML).toContain("Parity Status: Unknown");
    expect(card.shadowRoot?.innerHTML).not.toContain("Parity Check Needed");
    document.body.removeChild(card);
  });

  it("renders UnraidStorageCard using legacy sensor fallback when dedicated entities are absent", async () => {
    const card = new UnraidStorageCard();
    card.setConfig({ type: "custom:unraid-management-agent-storage-card" });
    const mockHass = createMockHass();
    delete mockHass.states["binary_sensor.cube_parity_valid"];
    delete mockHass.states["binary_sensor.cube_parity_check_running"];

    // Legacy off -> Parity Valid
    mockHass.states["binary_sensor.cube_parity_status"] = {
      entity_id: "binary_sensor.cube_parity_status",
      state: "off",
      attributes: { status: "completed" },
      last_changed: "",
      last_updated: "",
    };
    card.hass = withMockRegistry(mockHass);
    document.body.appendChild(card);
    await card.updateComplete;

    expect(card.shadowRoot?.innerHTML).toContain("Parity Valid");
    expect(card.shadowRoot?.innerHTML).toContain("Parity Status: Valid");

    // Legacy on with status running -> In Progress
    mockHass.states["binary_sensor.cube_parity_status"] = {
      entity_id: "binary_sensor.cube_parity_status",
      state: "on",
      attributes: { status: "running" },
      last_changed: "",
      last_updated: "",
    };
    mockHass.states["sensor.cube_parity_progress"] = {
      entity_id: "sensor.cube_parity_progress",
      state: "65",
      attributes: {},
      last_changed: "",
      last_updated: "",
    };
    card.hass = withMockRegistry({ ...mockHass });
    await card.updateComplete;

    expect(card.shadowRoot?.innerHTML).toContain("Parity Check In Progress (65%)");
    document.body.removeChild(card);
  });

  it("does not render unknown last check date text", async () => {
    const card = new UnraidStorageCard();
    card.setConfig({ type: "custom:unraid-management-agent-storage-card" });
    const mockHass = createMockHass();
    mockHass.states["sensor.cube_last_parity_check_date"] = {
      entity_id: "sensor.cube_last_parity_check_date",
      state: "unknown",
      attributes: {},
      last_changed: "",
      last_updated: "",
    };
    card.hass = withMockRegistry(mockHass);
    document.body.appendChild(card);
    await card.updateComplete;

    expect(card.shadowRoot?.innerHTML).not.toContain("Last check: unknown");
    expect(card.shadowRoot?.innerHTML).toContain("Parity healthy");
    document.body.removeChild(card);
  });

  it("renders UnraidSharesCard and handles protection states", async () => {
    const card = new UnraidSharesCard();
    card.setConfig({ type: "custom:unraid-management-agent-shares-card" });
    card.hass = createMockHass();
    document.body.appendChild(card);
    await card.updateComplete;

    expect(card.shadowRoot?.innerHTML).toContain("User Shares");
    expect(card.shadowRoot?.innerHTML).toContain("appdata");
    expect(card.shadowRoot?.innerHTML).toContain("media");
    expect(card.shadowRoot?.innerHTML).toContain("Protected");
    expect(card.shadowRoot?.innerHTML).toContain("46.6 GB");
    expect(card.shadowRoot?.innerHTML).toContain("480.6 GB");
    document.body.removeChild(card);
  });

  it("renders UnraidDockerCard and container list excluding autostart switches", async () => {
    const card = new UnraidDockerCard();
    card.setConfig({ type: "custom:unraid-management-agent-docker-card", view_mode: "list" });
    const hass = createMockHass();
    hass.states["switch.cube_docker_container_autostart_plex"] = {
      entity_id: "switch.cube_docker_container_autostart_plex",
      state: "on",
      attributes: { friendly_name: "plex Autostart" },
      last_changed: "",
      last_updated: "",
    };
    card.hass = withMockRegistry(hass);
    document.body.appendChild(card);
    await card.updateComplete;

    expect(card.shadowRoot?.innerHTML).toContain("Docker Containers");
    expect(card.shadowRoot?.innerHTML).toContain("plex");
    expect(card.shadowRoot?.innerHTML).not.toContain("plex Autostart");
    document.body.removeChild(card);
  });

  it("correctly formats UPS runtime for duration strings and numeric values", () => {
    expect(formatRuntime("1 hour 41 minutes")).toBe("1 hour 41 minutes");
    expect(formatRuntime("1 hour 41 minutes min")).toBe("1 hour 41 minutes");
    expect(formatRuntime("45 minutes min")).toBe("45 minutes");
    expect(formatRuntime("101")).toBe("1 hour 41 minutes");
    expect(formatRuntime("60")).toBe("1 hour");
    expect(formatRuntime("1")).toBe("1 minute");
    expect(formatRuntime("45")).toBe("45 minutes");
    expect(formatRuntime("3600", { unit_of_measurement: "s" })).toBe("1 hour");
    expect(formatRuntime("unavailable")).toBeNull();
    expect(formatRuntime("unknown")).toBeNull();
    expect(formatRuntime(null)).toBeNull();
  });

  it("renders UnraidUpsCard with battery, load, and properly formatted runtime", async () => {
    const card = new UnraidUpsCard();
    card.setConfig({ type: "custom:unraid-management-agent-ups-card" });
    const hass = createMockHass();
    hass.states["sensor.cube_ups_runtime"] = {
      entity_id: "sensor.cube_ups_runtime",
      state: "1 hour 41 minutes",
      attributes: {},
      last_changed: "",
      last_updated: "",
    };
    card.hass = withMockRegistry(hass);
    document.body.appendChild(card);
    await card.updateComplete;

    expect(card.shadowRoot?.innerHTML).toContain("UPS Power &amp; Battery");
    expect(card.shadowRoot?.innerHTML).toContain("100%");
    expect(card.shadowRoot?.innerHTML).toContain("1 hour 41 minutes");
    expect(card.shadowRoot?.innerHTML).not.toContain("1 hour 41 minutes min");
    document.body.removeChild(card);
  });

  it("renders UnraidVmCard with virtual machines", async () => {
    const card = new UnraidVmCard();
    card.setConfig({ type: "custom:unraid-management-agent-vm-card" });
    card.hass = createMockHass();
    document.body.appendChild(card);
    await card.updateComplete;

    expect(card.shadowRoot?.innerHTML).toContain("Virtual Machines");
    expect(card.shadowRoot?.innerHTML).toContain("Home Assistant");
    document.body.removeChild(card);
  });

  it("renders UnraidVmCard with VMs on child devices of the VMs device", async () => {
    const card = new UnraidVmCard();
    card.setConfig({ type: "custom:unraid-management-agent-vm-card" });
    const hass = createMockHass();
    hass.devices = {
      ...hass.devices,
      vms: {
        id: "vms",
        name: "CUBE VMs",
        identifiers: [["unraid_management_agent", "uuid-1234_vms"]],
        via_device_id: "dev_1",
      },
      win10: {
        id: "win10",
        name: "Windows 10",
        identifiers: [["unraid_management_agent", "uuid-1234_vm_win10"]],
        parent_device_id: "vms",
      },
      other: {
        id: "other",
        name: "OTHER",
        identifiers: [["unraid_management_agent", "uuid-9999"]],
      },
      other_vms: {
        id: "other_vms",
        name: "OTHER VMs",
        identifiers: [["unraid_management_agent", "uuid-9999_vms"]],
        via_device_id: "other",
      },
      other_vm: {
        id: "other_vm",
        name: "Gaming",
        identifiers: [["unraid_management_agent", "uuid-9999_vm_gaming"]],
        parent_device_id: "other_vms",
      },
      // Another integration's devices linked to the server
      foreign: {
        id: "foreign",
        name: "Hypervisor",
        identifiers: [["other_integration", "hypervisor"]],
        via_device_id: "dev_1",
      },
      foreign_child: {
        id: "foreign_child",
        name: "Guest",
        identifiers: [["other_integration", "guest"]],
        parent_device_id: "dev_1",
      },
    };
    // Entity IDs of VMs added under the VMs device have no "_vm_" in them
    // Only those on the server's devices count: not one without a device,
    // nor one on another server's or another integration's device
    const vmSwitches: Array<[string, string | null, string]> = [
      ["switch.cube_vms_windows_10_power", "win10", "Windows 10 Power"],
      ["switch.other_vms_gaming_power", "other_vm", "Gaming Power"],
      ["switch.other_kiosk_power", "other", "Kiosk Power"],
      ["switch.orphan_power", null, "Orphan Power"],
      ["switch.hypervisor_power", "foreign", "Hypervisor Power"],
      ["switch.guest_power", "foreign_child", "Guest Power"],
    ];
    for (const [entityId, deviceId, name] of vmSwitches) {
      hass.states[entityId] = {
        entity_id: entityId,
        state: "on",
        attributes: { friendly_name: name },
        last_changed: "",
        last_updated: "",
      };
      hass.entities![entityId] = {
        entity_id: entityId,
        device_id: deviceId,
        platform: "unraid_management_agent",
        translation_key: "vm_power",
      };
    }
    card.hass = withMockRegistry(hass);
    document.body.appendChild(card);
    await card.updateComplete;

    expect(card.shadowRoot?.innerHTML).toContain("Windows 10 Power");
    expect(card.shadowRoot?.innerHTML).not.toContain("Gaming Power");
    expect(card.shadowRoot?.innerHTML).not.toContain("Kiosk Power");
    expect(card.shadowRoot?.innerHTML).not.toContain("Orphan Power");
    expect(card.shadowRoot?.innerHTML).not.toContain("Hypervisor Power");
    expect(card.shadowRoot?.innerHTML).not.toContain("Guest Power");
    document.body.removeChild(card);
  });

  it("finds Container Updates Available on the Docker device", async () => {
    const card = new UnraidMaintenanceCard();
    card.setConfig({ type: "custom:unraid-management-agent-maintenance-card" });
    const hass = createMockHass();
    hass.devices = {
      ...hass.devices,
      docker: {
        id: "docker",
        name: "CUBE Docker",
        identifiers: [["unraid_management_agent", "uuid-1234_docker"]],
        via_device_id: "dev_1",
      },
    };
    const entityId = "binary_sensor.renamed_updates";
    hass.states[entityId] = {
      entity_id: entityId,
      state: "on",
      attributes: { friendly_name: "Updates", updates_available: 3 },
      last_changed: "",
      last_updated: "",
    };
    hass.entities![entityId] = {
      entity_id: entityId,
      device_id: "docker",
      platform: "unraid_management_agent",
      translation_key: "container_updates_available",
    };
    card.hass = withMockRegistry(hass);
    document.body.appendChild(card);
    await card.updateComplete;
    const found = (
      card as unknown as {
        getEntity: (key: string) => { entity_id: string } | undefined;
      }
    ).getEntity("container_updates_available");
    expect(found?.entity_id).toBe(entityId);
    document.body.removeChild(card);
  });

  it("prefers an entity on the server device over one on the Docker device", async () => {
    const card = new UnraidMaintenanceCard();
    card.setConfig({ type: "custom:unraid-management-agent-maintenance-card" });
    const hass = createMockHass();
    hass.devices = {
      ...hass.devices,
      docker: {
        id: "docker",
        name: "CUBE Docker",
        identifiers: [["unraid_management_agent", "uuid-1234_docker"]],
        via_device_id: "dev_1",
      },
    };
    // The Docker device's entity comes first in the registry
    const entities: Array<[string, string]> = [
      ["binary_sensor.docker_updates", "docker"],
      ["binary_sensor.server_updates", "dev_1"],
    ];
    for (const [entityId, deviceId] of entities) {
      hass.states[entityId] = {
        entity_id: entityId,
        state: "on",
        attributes: { friendly_name: "Updates", updates_available: 3 },
        last_changed: "",
        last_updated: "",
      };
      hass.entities![entityId] = {
        entity_id: entityId,
        device_id: deviceId,
        platform: "unraid_management_agent",
        translation_key: "container_updates_available",
      };
    }
    card.hass = withMockRegistry(hass);
    document.body.appendChild(card);
    await card.updateComplete;
    const found = (
      card as unknown as {
        getEntity: (key: string) => { entity_id: string } | undefined;
      }
    ).getEntity("container_updates_available");
    expect(found?.entity_id).toBe("binary_sensor.server_updates");
    document.body.removeChild(card);
  });

  it("renders UnraidDashboardCard with tabs", async () => {
    const card = new UnraidDashboardCard();
    card.setConfig({ type: "custom:unraid-management-agent-dashboard-card" });
    card.hass = createMockHass();
    document.body.appendChild(card);
    await card.updateComplete;

    expect(card.shadowRoot?.innerHTML).toContain("Unraid Management Agent");
    expect(card.shadowRoot?.innerHTML).toContain("Shares");
    document.body.removeChild(card);
  });

  it("renders UnraidServerCardEditor and updates config", async () => {
    const editor = new UnraidServerCardEditor();
    editor.setConfig({ type: "custom:unraid-management-agent-server-card", title: "My Tower" });
    editor.hass = createMockHass();
    document.body.appendChild(editor);
    await editor.updateComplete;

    const form = editor.shadowRoot?.querySelector("ha-form") as any;
    expect(form.computeLabel({ name: "server" })).toBe("Unraid Management Agent server");
    expect(form.schema.find((field: any) => field.name === "title").selector).toEqual({ text: {} });
    document.body.removeChild(editor);
  });

  it("does not offer the Docker and VMs devices or their children as servers", async () => {
    const hass = createMockHass();
    // Listed before the server: the Docker device links to it, containers and
    // VMs are child devices of the Docker and VMs devices
    hass.devices = {
      docker: {
        id: "docker",
        name: "CUBE Docker",
        identifiers: [["unraid_management_agent", "uuid-1234_docker"]],
        via_device_id: "dev_1",
      },
      plex: {
        id: "plex",
        name: "plex",
        identifiers: [["unraid_management_agent", "uuid-1234_container_plex"]],
        parent_device_id: "docker",
      },
      ...hass.devices,
    };
    const editor = new UnraidServerCardEditor();
    editor.setConfig({ type: "custom:unraid-management-agent-server-card" });
    editor.hass = hass;
    document.body.appendChild(editor);
    await editor.updateComplete;
    const form = editor.shadowRoot?.querySelector("ha-form") as any;
    const options = form.schema[0].selector.select.options;
    expect(options.map((o: any) => o.value)).toEqual(["", "dev_1"]);
    document.body.removeChild(editor);

    const card = new UnraidServerCard();
    card.setConfig({ type: "custom:unraid-management-agent-server-card" });
    card.hass = withMockRegistry(hass);
    document.body.appendChild(card);
    await card.updateComplete;
    expect(card.shadowRoot?.innerHTML).toContain("CUBE");
    expect(card.shadowRoot?.innerHTML).not.toContain("CUBE Docker");
    document.body.removeChild(card);
  });

  it("renders UnraidSharesCardEditor", async () => {
    const editor = new UnraidSharesCardEditor();
    editor.setConfig({ type: "custom:unraid-management-agent-shares-card", title: "My Shares" });
    editor.hass = createMockHass();
    document.body.appendChild(editor);
    await editor.updateComplete;

    const form = editor.shadowRoot?.querySelector("ha-form") as any;
    expect(form.computeLabel({ name: "server" })).toBe("Unraid Management Agent server");
    expect(form.schema.find((field: any) => field.name === "title").selector).toEqual({ text: {} });
    document.body.removeChild(editor);
  });

  it("renders UnraidServerCard with ISO timestamp uptime", async () => {
    const card = new UnraidServerCard();
    card.setConfig({ type: "custom:unraid-management-agent-server-card" });
    const hass = createMockHass();
    const threeHoursAgo = new Date(Date.now() - 3 * 3600 * 1000 - 15 * 60 * 1000).toISOString();
    hass.states["sensor.cube_up_since"] = {
      entity_id: "sensor.cube_up_since",
      state: threeHoursAgo,
      attributes: { friendly_name: "Cube Up since" },
      last_changed: "",
      last_updated: "",
    };
    card.hass = withMockRegistry(hass);
    document.body.appendChild(card);
    await card.updateComplete;

    expect(card.shadowRoot?.innerHTML).toContain("3h 15m");
    document.body.removeChild(card);
  });

  it("renders UnraidNetworkCard with interface list and traffic metrics", async () => {
    const card = new UnraidNetworkCard();
    card.setConfig({ type: "custom:unraid-management-agent-network-card" });
    card.hass = createMockHass();
    document.body.appendChild(card);
    await card.updateComplete;

    expect(card.shadowRoot?.innerHTML).toContain("Network");
    expect(card.shadowRoot?.innerHTML).toContain("eth0");
    expect(card.shadowRoot?.innerHTML).toContain("192.168.20.21");
    expect(card.shadowRoot?.innerHTML).toContain("1 Gbps");
    expect(card.shadowRoot?.innerHTML).toContain("12.40 MB/s");
    expect(card.shadowRoot?.innerHTML).toContain("5.80 MB/s");
    expect(card.shadowRoot?.innerHTML).toContain("1 Connected");
    document.body.removeChild(card);
  });

  it("handles shares with missing color attribute and clamps usage percentage", async () => {
    const card = new UnraidSharesCard();
    card.setConfig({ type: "custom:unraid-management-agent-shares-card" });
    const hass = createMockHass();
    // Add a share with missing color and >100% usage
    hass.states["sensor.cube_share_unprotected_usage"] = {
      entity_id: "sensor.cube_share_unprotected_usage",
      state: "105.0",
      attributes: {
        friendly_name: "Cube Share unprotected usage",
        used: "10.5 TB",
        total: "10.0 TB",
        free: "0 TB",
      },
      last_changed: "",
      last_updated: "",
    };
    card.hass = withMockRegistry(hass);
    document.body.appendChild(card);
    await card.updateComplete;

    expect(card.shadowRoot?.innerHTML).toContain("unprotected");
    expect(card.shadowRoot?.innerHTML).toContain("Unprotected");
    // Verify width is clamped to 100%
    expect(card.shadowRoot?.innerHTML).toContain("width: 100%");
    document.body.removeChild(card);
  });

  it("ignores network card child-device entities in UnraidNetworkCard", async () => {
    const card = new UnraidNetworkCard();
    card.setConfig({ type: "custom:unraid-management-agent-network-card" });
    const hass = createMockHass();
    hass.devices!["nic_1"] = {
      id: "nic_1",
      name: "Network card (41:00)",
      identifiers: [["unraid_management_agent", "entry_nic_0000:41:00"]],
    };
    // A NIC device without a model is named "Network card (bb:dd)", so its
    // port entities contain "_network_" like the interface entities do
    const nicEntities = [
      "sensor.cube_network_card_41_00_eth0_link_speed",
      "sensor.cube_network_card_41_00_eth0_rx_power",
      "binary_sensor.cube_network_card_41_00_eth0_optic",
    ];
    for (const entityId of nicEntities) {
      hass.states[entityId] = {
        entity_id: entityId,
        state: "10000",
        attributes: {},
        last_changed: "",
        last_updated: "",
      };
      hass.entities![entityId] = {
        entity_id: entityId,
        device_id: "nic_1",
        platform: "unraid_management_agent",
      };
    }
    hass.entities!["sensor.cube_network_eth0_speed"] = {
      entity_id: "sensor.cube_network_eth0_speed",
      device_id: "dev_1",
      platform: "unraid_management_agent",
    };
    card.hass = withMockRegistry(hass);
    document.body.appendChild(card);
    await card.updateComplete;

    const names = (
      card as unknown as { getNetworkInterfaces(): Array<{ name: string }> }
    )
      .getNetworkInterfaces()
      .map((iface) => iface.name);
    expect(names).toEqual(["eth0"]);
    expect(card.shadowRoot?.innerHTML).not.toContain("CARD_41_00");
    document.body.removeChild(card);
  });

  it("filters placeholder IP states from connected count and formats small data rates", async () => {
    const card = new UnraidNetworkCard();
    card.setConfig({ type: "custom:unraid-management-agent-network-card" });
    const hass = createMockHass();
    // Add an unavailable interface
    hass.states["sensor.cube_network_eth1_ip_address"] = {
      entity_id: "sensor.cube_network_eth1_ip_address",
      state: "unavailable",
      attributes: { friendly_name: "Cube Network eth1 IP" },
      last_changed: "",
      last_updated: "",
    };
    hass.states["binary_sensor.cube_network_eth1_link"] = {
      entity_id: "binary_sensor.cube_network_eth1_link",
      state: "off",
      attributes: {},
      last_changed: "",
      last_updated: "",
    };
    hass.states["sensor.cube_network_eth1_rx_throughput"] = {
      entity_id: "sensor.cube_network_eth1_rx_throughput",
      state: "0.05", // 0.05 MB/s = 50.0 kB/s
      attributes: {},
      last_changed: "",
      last_updated: "",
    };
    card.hass = withMockRegistry(hass);
    document.body.appendChild(card);
    await card.updateComplete;

    // eth0 is connected, eth1 is unavailable/off -> still 1 connected
    expect(card.shadowRoot?.innerHTML).toContain("1 Connected");
    expect(card.shadowRoot?.innerHTML).toContain("50.0 kB/s");
    expect(card.shadowRoot?.innerHTML).not.toContain("unavailable");

    // When throughput reports 'unknown' or 'unavailable', placeholder '--' is shown
    card.hass = {
      ...hass,
      states: {
        ...hass.states,
        "sensor.cube_network_eth1_rx_throughput": {
          ...hass.states["sensor.cube_network_eth1_rx_throughput"]!,
          state: "unavailable",
        },
      },
    };
    await card.updateComplete;
    expect(card.shadowRoot?.innerHTML).toContain("--");
    expect(card.shadowRoot?.innerHTML).not.toContain("unavailable");
    document.body.removeChild(card);
  });

  it("renders UnraidNetworkCardEditor", async () => {
    const editor = new UnraidNetworkCardEditor();
    editor.setConfig({ type: "custom:unraid-management-agent-network-card", title: "My Network" });
    editor.hass = createMockHass();
    document.body.appendChild(editor);
    await editor.updateComplete;

    const form = editor.shadowRoot?.querySelector("ha-form") as any;
    expect(form.computeLabel({ name: "server" })).toBe("Unraid Management Agent server");
    expect(form.schema.find((field: any) => field.name === "title").selector).toEqual({ text: {} });
    document.body.removeChild(editor);
  });

  it("renders UnraidZfsCard with pools and ARC hit ratio", async () => {
    const card = new UnraidZfsCard();
    card.setConfig({ type: "custom:unraid-management-agent-zfs-card" });
    card.hass = createMockHass();
    document.body.appendChild(card);
    await card.updateComplete;

    expect(card.shadowRoot?.innerHTML).toContain("95%");
    expect(card.shadowRoot?.innerHTML).toContain("ARC Hit Ratio");
    expect(card.shadowRoot?.innerHTML).toContain("tank");
    expect(card.shadowRoot?.innerHTML).toContain("4.2 TB / 10 TB");
    expect(card.shadowRoot?.innerHTML).toContain("42%");
    document.body.removeChild(card);
  });

  it("renders UnraidZfsCard pools shown as separate devices", async () => {
    const card = new UnraidZfsCard();
    card.setConfig({ type: "custom:unraid-management-agent-zfs-card" });
    const hass = createMockHass();
    hass.devices = {
      ...hass.devices,
      pool_flash: {
        id: "pool_flash",
        name: "ZFS pool · flash",
        identifiers: [["unraid_management_agent", "uuid-1234_zfs_pool_flash"]],
        parent_device_id: "dev_1",
      },
      other_server_pool: {
        id: "other_server_pool",
        name: "ZFS pool · elsewhere",
        identifiers: [["unraid_management_agent", "other_zfs_pool_elsewhere"]],
        parent_device_id: "dev_2",
      },
    };
    const add = (
      entityId: string,
      deviceId: string,
      translationKey: string,
      state: string,
      attributes: Record<string, unknown> = {}
    ) => {
      hass.states[entityId] = {
        entity_id: entityId,
        state,
        attributes,
        last_changed: "",
        last_updated: "",
      };
      hass.entities![entityId] = {
        entity_id: entityId,
        device_id: deviceId,
        platform: "unraid_management_agent",
        translation_key: translationKey,
      };
    };
    // New install: entity IDs follow the device name, not the pool name.
    add("sensor.cube_zfs_pool_flash_usage", "pool_flash", "zfs_pool_device_usage", "35", {
      pool_name: "flash",
      total_size: "1.9 TB",
      used_size: "660 GB",
    });
    add("sensor.cube_zfs_pool_flash_health", "pool_flash", "zfs_pool_device_health", "DEGRADED", {
      pool_name: "flash",
    });
    add(
      "sensor.cube_zfs_pool_flash_corrupted_files",
      "pool_flash",
      "zfs_pool_device_corrupted_files",
      "2"
    );
    add("sensor.elsewhere_usage", "other_server_pool", "zfs_pool_device_usage", "99", {
      pool_name: "elsewhere",
    });
    card.hass = withMockRegistry(hass);
    document.body.appendChild(card);
    await card.updateComplete;

    const html = card.shadowRoot?.innerHTML ?? "";
    expect(html).toContain("flash");
    expect(html).toContain("660 GB / 1.9 TB");
    expect(html).toContain("DEGRADED");
    expect(html).not.toContain("elsewhere");
    expect(html).not.toContain("pool_flash");
    document.body.removeChild(card);
  });

  it("keeps corrupted-file counts per pool on the server device", async () => {
    const card = new UnraidZfsCard();
    card.setConfig({ type: "custom:unraid-management-agent-zfs-card" });
    const hass = createMockHass();
    const add = (entityId: string, translationKey: string | undefined, state: string, attributes: Record<string, unknown> = {}) => {
      hass.states[entityId] = { entity_id: entityId, state, attributes, last_changed: "", last_updated: "" };
      hass.entities![entityId] = {
        entity_id: entityId,
        device_id: "dev_1",
        platform: "unraid_management_agent",
        translation_key: translationKey,
      };
    };
    add("sensor.cube_zfs_tank_usage", "zfs_pool_usage", "42", { pool_name: "tank" });
    add("sensor.cube_zfs_flash_usage", "zfs_pool_usage", "10", { pool_name: "flash" });
    add("sensor.cube_zfs_tank_corrupted_files", undefined, "3");
    add("sensor.cube_zfs_flash_corrupted_files", undefined, "0");
    card.hass = withMockRegistry(hass);
    const pools = (
      card as unknown as { getPools(): { name: string; corruptedFiles?: number }[] }
    ).getPools();
    expect(pools.find((p) => p.name === "tank")?.corruptedFiles).toBe(3);
    expect(pools.find((p) => p.name === "flash")?.corruptedFiles).toBe(0);
  });

  it("matches pools by pool_name after pool devices are turned off", async () => {
    const card = new UnraidZfsCard();
    card.setConfig({ type: "custom:unraid-management-agent-zfs-card" });
    const hass = createMockHass();
    const add = (entityId: string, translationKey: string | undefined, state: string, attributes: Record<string, unknown>) => {
      hass.states[entityId] = { entity_id: entityId, state, attributes, last_changed: "", last_updated: "" };
      hass.entities![entityId] = {
        entity_id: entityId,
        device_id: "dev_1",
        platform: "unraid_management_agent",
        translation_key: translationKey,
      };
    };
    // Created on a pool device, now back on the server: IDs say "pool_flash".
    add("sensor.cube_zfs_pool_flash_usage", "zfs_pool_usage", "35", { pool_name: "flash" });
    add("sensor.cube_zfs_pool_flash_health", "zfs_pool_health", "DEGRADED", { pool_name: "flash" });
    add("sensor.cube_zfs_pool_flash_corrupted_files", undefined, "4", { pool_name: "flash" });
    card.hass = withMockRegistry(hass);
    const pools = (
      card as unknown as {
        getPools(): { name: string; health: string; corruptedFiles?: number }[];
      }
    ).getPools();
    const flash = pools.filter((p) => p.name === "flash");
    expect(flash).toHaveLength(1);
    expect(flash[0]?.health).toBe("DEGRADED");
    expect(flash[0]?.corruptedFiles).toBe(4);
    expect(pools.map((p) => p.name)).not.toContain("pool_flash");
  });

  it("does not pick a child device as the server", async () => {
    const card = new UnraidZfsCard();
    card.setConfig({ type: "custom:unraid-management-agent-zfs-card" });
    const hass = createMockHass();
    hass.devices = {
      pool_flash: {
        id: "pool_flash",
        name: "ZFS pool · flash",
        identifiers: [["unraid_management_agent", "uuid-1234_zfs_pool_flash"]],
        parent_device_id: "dev_1",
      },
      ...hass.devices,
    };
    card.hass = withMockRegistry(hass);
    const active = (
      card as unknown as { getActiveDevice(): { id: string } | undefined }
    ).getActiveDevice();
    expect(active?.id).toBe("dev_1");
  });

  it("renders UnraidFansCard with cooling fan telemetry", async () => {
    const card = new UnraidFansCard();
    card.setConfig({ type: "custom:unraid-management-agent-fans-card" });
    card.hass = createMockHass();
    document.body.appendChild(card);
    await card.updateComplete;

    expect(card.shadowRoot?.innerHTML).toContain("Fan 1");
    expect(card.shadowRoot?.innerHTML).toContain("1200 RPM");
    expect(card.shadowRoot?.innerHTML).toContain("1 Fan");
    document.body.removeChild(card);
  });

  it("renders UnraidFansCard fans of a USB controller device", async () => {
    const card = new UnraidFansCard();
    card.setConfig({ type: "custom:unraid-management-agent-fans-card" });
    const hass = createMockHass();
    hass.devices = {
      ...hass.devices,
      octo: {
        id: "octo",
        name: "Octo (fan controller)",
        identifiers: [["unraid_management_agent", "uuid-1234_hwmon_octo_x"]],
        parent_device_id: "dev_1",
      },
      other_octo: {
        id: "other_octo",
        name: "Octo (fan controller)",
        identifiers: [["unraid_management_agent", "other_hwmon_octo_y"]],
        parent_device_id: "dev_2",
      },
    };
    const add = (entityId: string, deviceId: string, name: string, rpm: string) => {
      hass.states[entityId] = {
        entity_id: entityId,
        state: rpm,
        attributes: { friendly_name: name, unit_of_measurement: "RPM" },
        last_changed: "",
        last_updated: "",
      };
      hass.entities![entityId] = {
        entity_id: entityId,
        device_id: deviceId,
        platform: "unraid_management_agent",
      };
    };
    add("sensor.cube_fan_octo_fan8", "octo", "Octo (fan controller) Coolant Flow (rpm)", "742");
    add("sensor.other_fan_octo_fan1", "other_octo", "Other server fan", "999");
    card.hass = withMockRegistry(hass);
    document.body.appendChild(card);
    await card.updateComplete;

    const html = card.shadowRoot?.innerHTML ?? "";
    expect(html).toContain("742 RPM");
    expect(html).toContain("1200 RPM");
    expect(html).not.toContain("999 RPM");
    document.body.removeChild(card);
  });

  it("lists number-only fan controls of a USB controller device, not of another server", async () => {
    const card = new UnraidFansCard();
    card.setConfig({ type: "custom:unraid-management-agent-fans-card" });
    const hass = createMockHass();
    for (const id of Object.keys(hass.states)) {
      if (id.startsWith("sensor.") && id.includes("fan")) delete hass.states[id];
    }
    hass.devices = {
      ...hass.devices,
      octo: {
        id: "octo",
        name: "Octo (fan controller)",
        identifiers: [["unraid_management_agent", "uuid-1234_hwmon_octo_x"]],
        parent_device_id: "dev_1",
      },
      other_octo: {
        id: "other_octo",
        name: "Octo (fan controller)",
        identifiers: [["unraid_management_agent", "other_hwmon_octo_y"]],
        parent_device_id: "dev_2",
      },
    };
    const add = (entityId: string, deviceId: string, name: string, rpm: number) => {
      hass.states[entityId] = {
        entity_id: entityId,
        state: "50",
        attributes: { friendly_name: name, rpm, fan_id: entityId },
        last_changed: "",
        last_updated: "",
      };
      hass.entities![entityId] = {
        entity_id: entityId,
        device_id: deviceId,
        platform: "unraid_management_agent",
      };
    };
    add("number.cube_fan_octo_fan2", "octo", "Octo child fan", 1234);
    add("number.other_fan_octo_fan1", "other_octo", "Unrelated fan", 4321);
    card.hass = withMockRegistry(hass);
    document.body.appendChild(card);
    await card.updateComplete;

    const html = card.shadowRoot?.innerHTML ?? "";
    expect(html).toContain("1234 RPM");
    expect(html).not.toContain("4321 RPM");
    document.body.removeChild(card);
  });

  it("renders UnraidGpuCard with GPU loads and temperatures", async () => {
    const card = new UnraidGpuCard();
    card.setConfig({ type: "custom:unraid-management-agent-gpu-card" });
    card.hass = createMockHass();
    document.body.appendChild(card);
    await card.updateComplete;

    expect(card.shadowRoot?.innerHTML).toContain("NVIDIA RTX 3080");
    expect(card.shadowRoot?.innerHTML).toContain("45%");
    expect(card.shadowRoot?.innerHTML).toContain("55°C");
    document.body.removeChild(card);
  });

  it("renders UnraidGpuCard with named GPU slug entities like Intel UHD Graphics", async () => {
    const card = new UnraidGpuCard();
    card.setConfig({ type: "custom:unraid-management-agent-gpu-card" });
    const hass = createMockHass();
    // Add named GPU slug entities
    hass.states["sensor.cube_gpu_intel_uhd_graphics_630_utilization"] = {
      entity_id: "sensor.cube_gpu_intel_uhd_graphics_630_utilization",
      state: "15.0",
      attributes: {
        friendly_name: "Cube GPU Intel UHD Graphics 630 Utilization",
        gpu_name: "Intel UHD Graphics 630",
        gpu_driver_version: "6.18.38-Unraid",
      },
      last_changed: "",
      last_updated: "",
    };
    hass.states["sensor.cube_gpu_intel_uhd_graphics_630_temperature"] = {
      entity_id: "sensor.cube_gpu_intel_uhd_graphics_630_temperature",
      state: "42.0",
      attributes: {
        friendly_name: "Cube GPU Intel UHD Graphics 630 Temperature",
      },
      last_changed: "",
      last_updated: "",
    };
    hass.states["sensor.cube_gpu_intel_uhd_graphics_630_power"] = {
      entity_id: "sensor.cube_gpu_intel_uhd_graphics_630_power",
      state: "8.5",
      attributes: {
        friendly_name: "Cube GPU Intel UHD Graphics 630 Power",
      },
      last_changed: "",
      last_updated: "",
    };
    hass.states["sensor.cube_gpu_intel_uhd_graphics_630_energy"] = {
      entity_id: "sensor.cube_gpu_intel_uhd_graphics_630_energy",
      state: "1.25",
      attributes: {
        friendly_name: "Cube GPU Intel UHD Graphics 630 Energy",
      },
      last_changed: "",
      last_updated: "",
    };
    card.hass = withMockRegistry(hass);
    document.body.appendChild(card);
    await card.updateComplete;

    expect(card.shadowRoot?.innerHTML).toContain("Intel UHD Graphics 630");
    expect(card.shadowRoot?.innerHTML).toContain("15%");
    expect(card.shadowRoot?.innerHTML).toContain("42°C");
    expect(card.shadowRoot?.innerHTML).toContain("9W");
    expect(card.shadowRoot?.innerHTML).toContain("1.25 kWh");
    expect(card.shadowRoot?.innerHTML).toContain("6.18.38-Unraid");
    document.body.removeChild(card);
  });

  it("renders UnraidGpuCard with GPU sensors on GPU devices (GPUs as separate devices)", async () => {
    const card = new UnraidGpuCard();
    card.setConfig({ type: "custom:unraid-management-agent-gpu-card" });
    const hass = createMockHass();
    // Each GPU's sensors live on a "GPU · <name>" child device of the server.
    // A 4090 took index 0 from the 3070: the index-0 sensors kept their 3070
    // entity IDs and moved to the 4090's device, and the 3070's new index-1
    // sensors got "_2" suffixed entity IDs.
    hass.devices!["gpu_4090"] = {
      id: "gpu_4090",
      name: "GPU · NVIDIA GeForce RTX 4090",
      identifiers: [["unraid_management_agent", "uuid-1234_gpu_uuid_gpu-4090"]],
      parent_device_id: "dev_1",
    };
    hass.devices!["gpu_3070"] = {
      id: "gpu_3070",
      name: "GPU · NVIDIA GeForce RTX 3070",
      identifiers: [["unraid_management_agent", "uuid-1234_gpu_uuid_gpu-3070"]],
      parent_device_id: "dev_1",
    };
    hass.devices!["gpu_igpu"] = {
      id: "gpu_igpu",
      name: "GPU · Intel UHD Graphics 770",
      name_by_user: "Transcoder",
      identifiers: [["unraid_management_agent", "uuid-1234_gpu_pci_0000:00:02.0"]],
      parent_device_id: "dev_1",
    };
    // A GPU of another server must not show up
    hass.devices!["other_server"] = {
      id: "other_server",
      name: "Other",
      identifiers: [["unraid_management_agent", "uuid-9999"]],
    };
    hass.devices!["other_gpu"] = {
      id: "other_gpu",
      name: "GPU · NVIDIA GeForce RTX 5090",
      identifiers: [["unraid_management_agent", "uuid-9999_gpu_index_0"]],
      parent_device_id: "other_server",
    };
    const rtx3070 = "sensor.cube_gpu_nvidia_geforce_rtx_3070";
    const sensors: Array<[string, string, string, string, Record<string, unknown>]> = [
      [`${rtx3070}_utilization`, "gpu_4090", "88", "gpu_device_utilization", { gpu_name: "NVIDIA GeForce RTX 4090", gpu_driver_version: "615.78.08" }],
      [`${rtx3070}_temperature`, "gpu_4090", "71.0", "gpu_device_temperature", {}],
      [`${rtx3070}_vram_usage`, "gpu_4090", "50.0", "gpu_device_vram_usage", {}],
      [`${rtx3070}_vram_total`, "gpu_4090", "24.0", "gpu_device_vram_total", {}],
      [`${rtx3070}_utilization_2`, "gpu_3070", "12", "gpu_device_utilization", { gpu_name: "NVIDIA GeForce RTX 3070" }],
      [`${rtx3070}_temperature_2`, "gpu_3070", "61.0", "gpu_device_temperature", {}],
      ["sensor.cube_gpu_intel_uhd_graphics_770_temperature", "gpu_igpu", "38.0", "gpu_device_temperature", {}],
      ["sensor.cube_gpu_intel_uhd_graphics_770_utilization", "gpu_igpu", "7", "gpu_device_utilization", { gpu_name: "Intel UHD Graphics 770" }],
      ["sensor.other_gpu_nvidia_geforce_rtx_5090_utilization", "other_gpu", "99", "gpu_device_utilization", {}],
    ];
    for (const [entityId, deviceId, state, translationKey, attributes] of sensors) {
      hass.states[entityId] = {
        entity_id: entityId,
        state,
        attributes,
        last_changed: "",
        last_updated: "",
      };
      hass.entities![entityId] = {
        entity_id: entityId,
        device_id: deviceId,
        platform: "unraid_management_agent",
        translation_key: translationKey,
      };
    }
    // The server's own GPU sensors are still found by entity ID
    hass.entities!["sensor.cube_gpu_0_utilization"] = {
      entity_id: "sensor.cube_gpu_0_utilization",
      device_id: "dev_1",
      platform: "unraid_management_agent",
    };
    card.hass = withMockRegistry(hass);
    document.body.appendChild(card);
    await card.updateComplete;

    const html = card.shadowRoot?.innerHTML ?? "";
    const text = card.shadowRoot?.textContent?.replace(/\s+/g, " ") ?? "";
    expect(text).toContain("NVIDIA GeForce RTX 4090");
    expect(text).toContain("NVIDIA GeForce RTX 3070");
    expect(html).not.toContain("· NVIDIA");
    expect(html).toContain("71°C");
    expect(html).toContain("61°C");
    expect(html).toContain("615.78.08");
    // The name the user gave the GPU device wins over the GPU model
    expect(text).toContain("Transcoder");
    expect(text).not.toContain("Intel UHD Graphics 770");
    expect(html).toContain("38°C");
    expect(text).not.toContain("RTX 5090");
    expect(text).toContain("NVIDIA RTX 3080");
    expect(text).toContain("4 GPUs");
    document.body.removeChild(card);
  });

  it("renders UnraidGpuCard with GPU sensors on the server device (option off)", async () => {
    const card = new UnraidGpuCard();
    card.setConfig({ type: "custom:unraid-management-agent-gpu-card" });
    const hass = createMockHass();
    const sensors: Array<[string, string, string, Record<string, unknown>]> = [
      ["sensor.cube_gpu_nvidia_geforce_rtx_3070_utilization", "12", "gpu_utilization", { gpu_name: "NVIDIA GeForce RTX 3070", gpu_driver_version: "615.78.08" }],
      ["sensor.cube_gpu_nvidia_geforce_rtx_3070_temperature", "61.0", "gpu_temperature", {}],
      ["sensor.cube_gpu_nvidia_geforce_rtx_3070_vram_usage", "3.0", "gpu_vram_usage", {}],
    ];
    for (const [entityId, state, translationKey, attributes] of sensors) {
      const metric = translationKey.replace("gpu_", "").replace("vram_usage", "VRAM Usage");
      hass.states[entityId] = {
        entity_id: entityId,
        state,
        attributes: {
          friendly_name: `CUBE GPU NVIDIA GeForce RTX 3070 ${metric.charAt(0).toUpperCase()}${metric.slice(1)}`,
          ...attributes,
        },
        last_changed: "",
        last_updated: "",
      };
      hass.entities![entityId] = {
        entity_id: entityId,
        device_id: "dev_1",
        platform: "unraid_management_agent",
        translation_key: translationKey,
      };
    }
    card.hass = withMockRegistry(hass);
    document.body.appendChild(card);
    await card.updateComplete;

    const html = card.shadowRoot?.innerHTML ?? "";
    const text = card.shadowRoot?.textContent?.replace(/\s+/g, " ") ?? "";
    expect(text).toContain("NVIDIA GeForce RTX 3070");
    expect(html).toContain("61°C");
    expect(html).toContain("615.78.08");
    expect(text).toContain("NVIDIA RTX 3080");
    expect(text).toContain("2 GPUs");
    document.body.removeChild(card);
  });

  it("renders UnraidGpuCard with suffixed sensors on the server device after an index shift", async () => {
    const card = new UnraidGpuCard();
    card.setConfig({ type: "custom:unraid-management-agent-gpu-card" });
    const hass = createMockHass();
    // A 4090 took index 0: the index-0 sensors kept their 3070 entity IDs, and
    // the 3070's index-1 sensors got "_2" suffixed entity IDs
    const rtx3070 = "sensor.cube_gpu_nvidia_geforce_rtx_3070";
    const sensors: Array<[string, string, string, Record<string, unknown>]> = [
      [`${rtx3070}_utilization`, "88", "CUBE GPU NVIDIA GeForce RTX 4090 Utilization", { gpu_name: "NVIDIA GeForce RTX 4090" }],
      [`${rtx3070}_temperature`, "71.0", "CUBE GPU NVIDIA GeForce RTX 4090 Temperature", {}],
      [`${rtx3070}_utilization_2`, "12", "CUBE GPU NVIDIA GeForce RTX 3070 Utilization", { gpu_name: "NVIDIA GeForce RTX 3070" }],
      [`${rtx3070}_temperature_2`, "61.0", "CUBE GPU NVIDIA GeForce RTX 3070 Temperature", {}],
    ];
    for (const [entityId, state, friendlyName, attributes] of sensors) {
      hass.states[entityId] = {
        entity_id: entityId,
        state,
        attributes: { friendly_name: friendlyName, ...attributes },
        last_changed: "",
        last_updated: "",
      };
      hass.entities![entityId] = {
        entity_id: entityId,
        device_id: "dev_1",
        platform: "unraid_management_agent",
      };
    }
    card.hass = withMockRegistry(hass);
    document.body.appendChild(card);
    await card.updateComplete;

    const html = card.shadowRoot?.innerHTML ?? "";
    const text = card.shadowRoot?.textContent?.replace(/\s+/g, " ") ?? "";
    expect(text).toContain("NVIDIA GeForce RTX 4090");
    expect(text).toContain("NVIDIA GeForce RTX 3070");
    expect(html).toContain("71°C");
    expect(html).toContain("61°C");
    expect(text).toContain("3 GPUs");
    document.body.removeChild(card);
  });

  it("never offers or picks a child device as the Unraid server", async () => {
    const card = new UnraidGpuCard();
    card.setConfig({ type: "custom:unraid-management-agent-gpu-card" });
    const hass = createMockHass();
    // Child devices can be listed before their server device
    hass.devices = {
      gpu_3070: {
        id: "gpu_3070",
        name: "GPU · NVIDIA GeForce RTX 3070",
        identifiers: [["unraid_management_agent", "uuid-1234_gpu_uuid_gpu-3070"]],
        parent_device_id: "dev_1",
      },
      ...hass.devices,
    };
    card.hass = withMockRegistry(hass);
    document.body.appendChild(card);
    await card.updateComplete;
    expect(card.shadowRoot?.innerHTML).toContain("CUBE");
    document.body.removeChild(card);

    const editor = new UnraidGpuCardEditor();
    editor.hass = hass;
    editor.setConfig({ type: "custom:unraid-management-agent-gpu-card" });
    document.body.appendChild(editor);
    await editor.updateComplete;
    const form = editor.shadowRoot?.querySelector("ha-form") as any;
    expect(form.schema[0].selector.select.options.map((option: any) => option.label)).toEqual([
      "Automatically select an Agent server", "CUBE",
    ]);
    document.body.removeChild(editor);
  });

  it("renders UnraidNotificationsCard with unread counts", async () => {
    const card = new UnraidNotificationsCard();
    card.setConfig({ type: "custom:unraid-management-agent-notifications-card" });
    card.hass = createMockHass();
    document.body.appendChild(card);
    await card.updateComplete;

    expect(card.shadowRoot?.innerHTML).toContain("Notifications Center");
    expect(card.shadowRoot?.innerHTML).toContain("Critical Issues");
    expect(card.shadowRoot?.innerHTML).toContain("Action Required");
    document.body.removeChild(card);
  });

  it("renders UnraidMaintenanceCard with flash and parity telemetry", async () => {
    const card = new UnraidMaintenanceCard();
    card.setConfig({ type: "custom:unraid-management-agent-maintenance-card" });
    card.hass = createMockHass();
    document.body.appendChild(card);
    await card.updateComplete;

    expect(card.shadowRoot?.innerHTML).toContain("Maintenance &amp; Operations");
    expect(card.shadowRoot?.innerHTML).toContain("Flash Boot Drive");
    expect(card.shadowRoot?.innerHTML).toContain("Parity Health");
    document.body.removeChild(card);
  });

  it("renders UnraidRemoteSharesCard with remote share usage and mount status", async () => {
    const card = new UnraidRemoteSharesCard();
    card.setConfig({ type: "custom:unraid-management-agent-remote-shares-card" });
    card.hass = createMockHass();
    document.body.appendChild(card);
    await card.updateComplete;

    expect(card.shadowRoot?.innerHTML).toContain("backup");
    expect(card.shadowRoot?.innerHTML).toContain("350 GB / 1 TB");
    expect(card.shadowRoot?.innerHTML).toContain("35%");
    document.body.removeChild(card);
  });

  it("renders UnraidUnassignedDevicesCard with external disks", async () => {
    const card = new UnraidUnassignedDevicesCard();
    card.setConfig({ type: "custom:unraid-management-agent-unassigned-devices-card" });
    card.hass = createMockHass();
    document.body.appendChild(card);
    await card.updateComplete;

    expect(card.shadowRoot?.innerHTML).toContain("dev1");
    expect(card.shadowRoot?.innerHTML).toContain("2 TB");
    expect(card.shadowRoot?.innerHTML).toContain("MOUNTED");
    document.body.removeChild(card);
  });
});


describe("Unraid Management Agent isolation", () => {
  it("registers 15 branded cards and editors without claiming generic Unraid tags", () => {
    expect(window.customCards).toHaveLength(15);
    for (const card of window.customCards ?? []) {
      expect(card.type).toMatch(/^unraid-management-agent-/);
      expect(card.name).toMatch(/^Unraid Management Agent /);
      expect(card.preview).toBe(false);
      expect(customElements.get(`${card.type}-editor`)).toBeDefined();
      expect(customElements.get(card.type.replace("unraid-management-agent-", "unraid-"))).toBeUndefined();
    }
  });

  it("ignores same-name Unraid servers, foreign entities on Agent devices, and unknown ownership", () => {
    const hass = createMockHass();
    hass.devices!.foreign = { id: "foreign", name: "CUBE", identifiers: [["unraid", "other"]] };
    const ids = ["switch.cube_container_foreign", "switch.cube_container_spoof", "switch.cube_container_unknown"];
    for (const entity_id of ids) {
      hass.states[entity_id] = { entity_id, state: "on", attributes: { friendly_name: "Foreign container" }, last_changed: "", last_updated: "" };
    }
    hass.entities![ids[0]!] = { entity_id: ids[0]!, platform: "unraid", device_id: "foreign", translation_key: "docker_container" };
    hass.entities![ids[1]!] = { entity_id: ids[1]!, platform: "unraid", device_id: "dev_1", translation_key: "docker_container" };
    const card = new UnraidDockerCard() as any;
    card.setConfig({ type: "custom:unraid-management-agent-docker-card" });
    card.hass = hass;
    expect(card.getUnraidDevices().map((d: any) => d.id)).toEqual(["dev_1"]);
    expect(card.getContainers().map((c: any) => c.name)).not.toContain("Foreign container");
    expect(card.findEntity(ids[0])).toBeUndefined();
    expect(card.findEntity(/container_foreign/)).toBeUndefined();
    expect(card.getEntity("container_foreign", "switch")).toBeUndefined();
    expect(card.getEntities("docker_container").map((s: any) => s.entity_id)).not.toEqual(expect.arrayContaining(ids));
  });

  it("fails closed for missing/partial registries and an explicitly missing server", () => {
    const card = new UnraidDockerCard() as any;
    const hass = createMockHass();
    card.setConfig({ type: "custom:unraid-management-agent-docker-card" });
    card.hass = { ...hass, entities: undefined };
    expect(card.getContainers()).toEqual([]);
    card.hass = { ...hass, entities: {} };
    expect(card.getContainers()).toEqual([]);
    card.hass = hass;
    card.setConfig({ type: "custom:unraid-management-agent-docker-card", server: "missing" });
    expect(card.getActiveDevice()).toBeUndefined();
    expect(card.getContainers()).toEqual([]);
    expect(UnraidDockerCard.getStubConfig(hass)).toEqual({ server: "dev_1" });
  });

  it("walks shuffled descendants recursively and leaves foreign or cyclic trees out", () => {
    const hass = createMockHass();
    const device = (id: string, parent: string, foreign = false) => ({ id, name: id, identifiers: [[foreign ? "unraid" : "unraid_management_agent", id]] as [string,string][], parent_device_id: parent });
    hass.devices = {
      deep: device("deep", "nested"), nested: device("nested", "docker"),
      docker: { ...device("docker", "dev_1"), via_device_id: "dev_1", parent_device_id: undefined },
      foreign: device("foreign", "dev_1", true),
      cycle_a: device("cycle_a", "cycle_b"), cycle_b: device("cycle_b", "cycle_a"),
      ...hass.devices,
    };
    const card = new UnraidDockerCard() as any;
    card.setConfig({ type: "custom:unraid-management-agent-docker-card" }); card.hass = hass;
    expect([...card.getServerDeviceIds("dev_1")].sort()).toEqual(["deep", "dev_1", "docker", "nested"]);
  });

  it("does not dispatch stale or foreign controls and uses explicit container actions", async () => {
    const hass = createMockHass(); hass.callService = vi.fn(async () => undefined);
    const card = new UnraidDockerCard() as any;
    card.setConfig({ type: "custom:unraid-management-agent-docker-card" }); card.hass = hass;
    await card.toggleEntity("switch.foreign_container"); await card.pressButton("button.foreign_restart");
    expect(hass.callService).not.toHaveBeenCalled();
    const own = Object.keys(hass.states).find((id) => id.startsWith("switch.") && id.includes("container"))!;
    await card.runContainerAction(own, "start");
    expect(hass.callService).toHaveBeenCalledExactlyOnceWith("switch", "turn_on", { entity_id: own });
    card.handleToggle(own, true, "Own container");
    expect(hass.callService).toHaveBeenCalledTimes(1);
    expect(card._pendingAction.action).toBe("stop");
  });

  it("offers only Agent roots in native editor controls and round-trips existing settings", async () => {
    const hass = createMockHass();
    hass.devices!.foreign = { id: "foreign", name: "Other Unraid", identifiers: [["unraid", "other"]] };
    const editor = new UnraidServerCardEditor(); editor.hass = hass;
    editor.setConfig({ type: "custom:unraid-management-agent-server-card", server: "CUBE", title: "Old", hide_header: true });
    document.body.append(editor); await editor.updateComplete;
    const form = editor.shadowRoot!.querySelector("ha-form") as any;
    expect(form.data.server).toBe("dev_1");
    expect(form.schema[0].selector.select.options.map((v: any) => v.value)).toEqual(["", "dev_1"]);
    const changed = vi.fn(); editor.addEventListener("config-changed", changed);
    form.dispatchEvent(new CustomEvent("value-changed", { detail: { value: { server: "dev_1", title: "" } }, bubbles: true, composed: true }));
    expect(changed.mock.calls[0]![0].detail.config).toEqual({ type: "custom:unraid-management-agent-server-card", server: "dev_1", hide_header: true });
    editor.remove();
  });

  it("does not add unsupported defaults when a native form emits all of its data", async () => {
    const editor = new UnraidSharesCardEditor(); editor.hass = createMockHass();
    editor.setConfig({ type: "custom:unraid-management-agent-shares-card" });
    document.body.append(editor); await editor.updateComplete;
    const form = editor.shadowRoot!.querySelector("ha-form") as any;
    expect(form.data).not.toHaveProperty("view_mode");
    expect(form.data).not.toHaveProperty("show_system_info");
    const changed = vi.fn(); editor.addEventListener("config-changed", changed);
    form.dispatchEvent(new CustomEvent("value-changed", { detail: { value: { ...form.data, title: "Shares" } }, bubbles: true, composed: true }));
    expect(changed.mock.calls[0]![0].detail.config).toEqual({ type: "custom:unraid-management-agent-shares-card", title: "Shares" });
    editor.remove();
  });


  it("keeps distinctive container names visible without renaming entities", () => {
    const hass = createMockHass();
    const entity = Object.values(hass.states).find((state) => state.entity_id.startsWith("switch.") && state.entity_id.includes("container"))!;
    entity.attributes.friendly_name = "CUBE Container ci-runner-1";
    const card = new UnraidDockerCard() as any;
    card.setConfig({ type: "custom:unraid-management-agent-docker-card" }); card.hass = hass;
    const container = card.getContainers().find((c: any) => c.switchEntityId === entity.entity_id);
    expect(container.name).toBe("ci-runner-1");
    expect(entity.attributes.friendly_name).toBe("CUBE Container ci-runner-1");
    entity.attributes.friendly_name = "CUBE custom name";
    expect(card.getContainers().find((c: any) => c.switchEntityId === entity.entity_id).name).toBe("CUBE custom name");
  });

});
