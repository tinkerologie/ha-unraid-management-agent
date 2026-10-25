import { describe, it, expect, beforeAll } from "vitest";
import liveDataJson from "./live-states.json";
import "../src/index";
import { UnraidServerCard } from "../src/server-card";
import { UnraidStorageCard } from "../src/storage-card";
import { UnraidSharesCard } from "../src/shares-card";
import { UnraidDockerCard } from "../src/docker-card";
import { UnraidUpsCard } from "../src/ups-card";
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

describe("Live Server Cube Cards Verification", () => {
  let liveData: { device: any; states: Record<string, any> };
  let mockHass: any;

  beforeAll(() => {
    liveData = structuredClone(liveDataJson) as unknown as { device: any; states: Record<string, any> };
    // The recorded telemetry is reused with explicit Agent ownership.
    liveData.device.id = liveData.device.device_id;
    liveData.device.identifiers = [["unraid_management_agent", "fixture-agent"]];

    mockHass = {
      states: liveData.states,
      devices: {
        [liveData.device.id || "9ea58bac337a54169c3d2181f36be095"]: liveData.device,
      },
      entities: {},
      formatEntityState: (entity: any) => entity?.state || "",
      formatEntityAttributeValue: (_entity: any, attr: string) => attr,
      callService: async () => {},
    };

    // Populate hass.entities
    for (const [entityId, stateObj] of Object.entries(liveData.states)) {
      mockHass.entities[entityId] = {
        entity_id: entityId,
        device_id: liveData.device.id || "9ea58bac337a54169c3d2181f36be095",
        platform: "unraid_management_agent",
        translation_key: (stateObj as any).attributes?.translation_key,
      };
    }
  });

  it("verifies UnraidGpuCard renders live GPU telemetry", async () => {
    const card = new UnraidGpuCard();
    card.setConfig({ type: "custom:unraid-management-agent-gpu-card", server: "Cube" });
    card.hass = mockHass;
    document.body.appendChild(card);
    await card.updateComplete;

    const html = card.shadowRoot?.innerHTML || "";
    // Verify GPU is detected
    expect(html).not.toContain("No GPU Telemetry Available");
    expect(html).toContain("Intel UHD Graphics 630");
    expect(html).toContain("GPU Load");
    expect(html).toContain("Temperature");
    expect(html).toContain("Power Draw");
    expect(html).toContain("6.18.38-Unraid");
    document.body.removeChild(card);
  });

  it("verifies UnraidServerCard renders live server metrics", async () => {
    const card = new UnraidServerCard();
    card.setConfig({ type: "custom:unraid-management-agent-server-card", server: "Cube" });
    card.hass = mockHass;
    document.body.appendChild(card);
    await card.updateComplete;

    const html = card.shadowRoot?.innerHTML || "";
    expect(html).toContain("Cube");
    expect(html).toContain("CPU");
    expect(html).toContain("Memory");
    document.body.removeChild(card);
  });

  it("verifies UnraidStorageCard renders live array and disk data", async () => {
    const card = new UnraidStorageCard();
    card.setConfig({ type: "custom:unraid-management-agent-storage-card", server: "Cube" });
    card.hass = mockHass;
    document.body.appendChild(card);
    await card.updateComplete;

    const html = card.shadowRoot?.innerHTML || "";
    expect(html).toContain("Storage");
    expect(html).toContain("Disk 1");
    document.body.removeChild(card);
  });

  it("verifies UnraidSharesCard renders live shares", async () => {
    const card = new UnraidSharesCard();
    card.setConfig({ type: "custom:unraid-management-agent-shares-card", server: "Cube" });
    card.hass = mockHass;
    document.body.appendChild(card);
    await card.updateComplete;

    const html = card.shadowRoot?.innerHTML || "";
    expect(html).toContain("User Shares");
    expect(html).toContain("appdata");
    expect(html).toContain("media");
    document.body.removeChild(card);
  });

  it("verifies UnraidDockerCard renders live docker containers", async () => {
    const card = new UnraidDockerCard();
    card.setConfig({ type: "custom:unraid-management-agent-docker-card", server: "Cube" });
    card.hass = mockHass;
    document.body.appendChild(card);
    await card.updateComplete;

    const html = card.shadowRoot?.innerHTML || "";
    expect(html).toContain("Containers");
    expect(html).toContain("plex");
    expect(html).toContain("homeassistant");
    document.body.removeChild(card);
  });

  it("verifies UnraidUpsCard renders live UPS telemetry", async () => {
    const card = new UnraidUpsCard();
    card.setConfig({ type: "custom:unraid-management-agent-ups-card", server: "Cube" });
    card.hass = mockHass;
    document.body.appendChild(card);
    await card.updateComplete;

    const html = card.shadowRoot?.innerHTML || "";
    expect(html).toContain("Battery");
    expect(html).toContain("Load");
    document.body.removeChild(card);
  });

  it("verifies UnraidVmCard renders live VMs", async () => {
    const card = new UnraidVmCard();
    card.setConfig({ type: "custom:unraid-management-agent-vm-card", server: "Cube" });
    card.hass = mockHass;
    document.body.appendChild(card);
    await card.updateComplete;

    const html = card.shadowRoot?.innerHTML || "";
    expect(html).toContain("Virtual Machines");
    document.body.removeChild(card);
  });

  it("verifies UnraidNetworkCard renders live network interfaces", async () => {
    const card = new UnraidNetworkCard();
    card.setConfig({ type: "custom:unraid-management-agent-network-card", server: "Cube" });
    card.hass = mockHass;
    document.body.appendChild(card);
    await card.updateComplete;

    const html = card.shadowRoot?.innerHTML || "";
    expect(html).toContain("Network");
    document.body.removeChild(card);
  });

  it("verifies UnraidFansCard renders live cooling telemetry", async () => {
    const card = new UnraidFansCard();
    card.setConfig({ type: "custom:unraid-management-agent-fans-card", server: "Cube" });
    card.hass = mockHass;
    document.body.appendChild(card);
    await card.updateComplete;

    const html = card.shadowRoot?.innerHTML || "";
    expect(html).toContain("Cooling");
    document.body.removeChild(card);
  });

  it("verifies UnraidNotificationsCard renders live notification center", async () => {
    const card = new UnraidNotificationsCard();
    card.setConfig({ type: "custom:unraid-management-agent-notifications-card", server: "Cube" });
    card.hass = mockHass;
    document.body.appendChild(card);
    await card.updateComplete;

    const html = card.shadowRoot?.innerHTML || "";
    expect(html).toContain("Notifications Center");
    document.body.removeChild(card);
  });

  it("verifies UnraidMaintenanceCard renders live maintenance operations", async () => {
    const card = new UnraidMaintenanceCard();
    card.setConfig({ type: "custom:unraid-management-agent-maintenance-card", server: "Cube" });
    card.hass = mockHass;
    document.body.appendChild(card);
    await card.updateComplete;

    const html = card.shadowRoot?.innerHTML || "";
    expect(html).toContain("Flash");
    document.body.removeChild(card);
  });

  it("verifies UnraidDashboardCard renders tabs with live data", async () => {
    const card = new UnraidDashboardCard();
    card.setConfig({ type: "custom:unraid-management-agent-dashboard-card", server: "Cube" });
    card.hass = mockHass;
    document.body.appendChild(card);
    await card.updateComplete;

    const html = card.shadowRoot?.innerHTML || "";
    expect(html).toContain("Overview");
    expect(html).toContain("Storage");
    expect(html).toContain("Docker");
    expect(html).toContain("GPU");
    document.body.removeChild(card);
  });

  it("verifies UnraidZfsCard renders correctly", async () => {
    const card = new UnraidZfsCard();
    card.setConfig({ type: "custom:unraid-management-agent-zfs-card", server: "Cube" });
    card.hass = mockHass;
    document.body.appendChild(card);
    await card.updateComplete;

    const html = card.shadowRoot?.innerHTML || "";
    expect(html).toContain("ZFS");
    document.body.removeChild(card);
  });

  it("verifies UnraidRemoteSharesCard renders correctly", async () => {
    const card = new UnraidRemoteSharesCard();
    card.setConfig({ type: "custom:unraid-management-agent-remote-shares-card", server: "Cube" });
    card.hass = mockHass;
    document.body.appendChild(card);
    await card.updateComplete;

    const html = card.shadowRoot?.innerHTML || "";
    expect(html).toContain("Remote Shares");
    document.body.removeChild(card);
  });

  it("verifies UnraidUnassignedDevicesCard renders correctly", async () => {
    const card = new UnraidUnassignedDevicesCard();
    card.setConfig({ type: "custom:unraid-management-agent-unassigned-devices-card", server: "Cube" });
    card.hass = mockHass;
    document.body.appendChild(card);
    await card.updateComplete;

    const html = card.shadowRoot?.innerHTML || "";
    expect(html).toContain("Unassigned");
    document.body.removeChild(card);
  });
});
