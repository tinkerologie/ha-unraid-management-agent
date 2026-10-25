import { LitElement, html, nothing, type PropertyValues, type TemplateResult } from "lit";
import { type CardConfig } from "./config";
import { dashboardCardStyles } from "./dashboard-cards-styles";
import {
  fireEvent,
  type DeviceRegistryEntry,
  type HassEntity,
  type HomeAssistant,
} from "./ha-types";
import { iconTemplate } from "./icons";

/**
 * Format timestamp into human-friendly date string (e.g. "Jan 13, 2026, 15:16").
 */
export function formatFriendlyDateTime(value: string | undefined): string {
  if (!value || value === "unavailable" || value === "unknown") return "--";
  if (value.includes("T") || /^\d{4}-\d{2}-\d{2}/.test(value)) {
    try {
      const d = new Date(value);
      if (!isNaN(d.getTime())) {
        return (
          d.toLocaleDateString(undefined, {
            month: "short",
            day: "numeric",
            year: "numeric",
          }) +
          ", " +
          d.toLocaleTimeString(undefined, {
            hour: "2-digit",
            minute: "2-digit",
            hour12: false,
          })
        );
      }
    } catch {
      // Fallback
    }
  }
  return value;
}

export abstract class BaseUnraidCard extends LitElement {
  static override styles = dashboardCardStyles;
  static editorTag = "";

  static async getConfigElement(this: {
    editorTag: string;
  }): Promise<HTMLElement> {
    return document.createElement(this.editorTag);
  }

  static getStubConfig(hass?: HomeAssistant): Record<string, unknown> {
    const server = Object.values(hass?.devices ?? {}).find(
      (device) =>
        !device.via_device_id &&
        !device.parent_device_id &&
        device.identifiers?.some(([domain]) => domain === "unraid_management_agent")
    );
    return server ? { server: server.id } : {};
  }

  static override properties = {
    hass: { attribute: false },
    config: { attribute: false },
  };

  declare hass?: HomeAssistant;
  declare config: CardConfig;
  private _agentStates?: Record<string, HassEntity>;
  private _agentStatesHass?: HomeAssistant;
  private _agentStatesConfig?: CardConfig;

  constructor() {
    super();
    this.config = { type: "" };
  }

  protected slugifyDeviceName(name: string): string {
    return name
      .normalize("NFKD")
      .replace(/[\u0300-\u036f]/g, "")
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, "_")
      .replace(/^_+|_+$/g, "");
  }

  override willUpdate(changedProperties: PropertyValues<this>): void {
    super.willUpdate(changedProperties);
    this._agentStates = undefined;
    if (changedProperties.has("config")) {
      if (this.config.embedded) {
        this.setAttribute("embedded", "");
      } else {
        this.removeAttribute("embedded");
      }
    }
  }

  setConfig(config: CardConfig): void {
    if (!config || typeof config.type !== "string") {
      throw new Error("Invalid card configuration");
    }
    this.config = { ...config };
    if (this.config.embedded) {
      this.setAttribute("embedded", "");
    } else {
      this.removeAttribute("embedded");
    }
  }

  getCardSize(): number {
    return 4;
  }

  getGridOptions() {
    return { columns: 12, min_columns: 6 };
  }

  /** Get all Unraid server devices registered in Home Assistant */
  protected getUnraidDevices(): DeviceRegistryEntry[] {
    if (!this.hass?.devices) return [];
    return Object.values(this.hass.devices).filter(
      (device) =>
        // Child devices (GPUs, storage) of a server, and the Docker and VMs
        // devices (linked to their server) with their child devices
        // (containers, VMs), are not servers
        !device.via_device_id &&
        !device.parent_device_id &&
        this.isUnraidDevice(device)
    );
  }

  /** Whether a device was registered by this integration */
  protected isUnraidDevice(device: DeviceRegistryEntry): boolean {
    return (
      device.identifiers?.some(
        ([domain]) => domain === "unraid_management_agent"
      ) ?? false
    );
  }


  /** Resolve the active Unraid device based on config or default */
  protected getActiveDevice(): DeviceRegistryEntry | undefined {
    const devices = this.getUnraidDevices();
    if (devices.length === 0) return undefined;

    if (this.config.server) {
      const match = devices.find(
        (d) =>
          d.id === this.config.server ||
          d.name?.toLowerCase() === this.config.server?.toLowerCase() ||
          d.name_by_user?.toLowerCase() === this.config.server?.toLowerCase()
      );
      if (match) return match;
    }
    return this.config.server ? undefined : devices[0];
  }

  /** Only expose entities owned by the selected Agent server and its devices. */
  protected get agentStates(): Record<string, HassEntity> {
    if (
      this._agentStates && this._agentStatesHass === this.hass &&
      this._agentStatesConfig === this.config
    ) return this._agentStates;
    const server = this.getActiveDevice();
    if (!server || !this.hass?.entities) return {};
    const deviceIds = this.getServerDeviceIds(server.id);
    this._agentStatesHass = this.hass;
    this._agentStatesConfig = this.config;
    this._agentStates = Object.fromEntries(
      Object.entries(this.hass.states).filter(([entityId]) => {
        const entry = this.hass?.entities?.[entityId];
        return (
          entry?.platform === "unraid_management_agent" &&
          !!entry.device_id &&
          deviceIds.has(entry.device_id)
        );
      })
    );
    return this._agentStates;
  }

  /**
   * IDs of the server device and this integration's devices under it: its
   * child devices (GPUs, storage), its Docker and VMs devices (linked to it)
   * and their child devices (containers and VMs). Devices of other
   * integrations linked to the server are left out.
   */
  protected getServerDeviceIds(serverId: string): Set<string> {
    const ids = new Set([serverId]);
    const devices = Object.values(this.hass?.devices ?? {}).filter((device) =>
      this.isUnraidDevice(device)
    );
    let added = true;
    while (added) {
      added = false;
      for (const device of devices) {
        if (
          !ids.has(device.id) &&
          ((device.via_device_id && ids.has(device.via_device_id)) ||
            (device.parent_device_id && ids.has(device.parent_device_id)))
        ) {
          ids.add(device.id);
          added = true;
        }
      }
    }
    return ids;
  }

  /** True when a device is the given server device or one of its child devices */
  protected isServerOrChildDevice(deviceId: string, serverId: string): boolean {
    return this.getServerDeviceIds(serverId).has(deviceId);
  }

  /**
   * Find an entity by translation key or entity_id suffix.
   */
  protected getEntity(
    translationKey: string,
    domain?: string
  ): HassEntity | undefined {
    if (!this.hass?.states) return undefined;
    const device = this.getActiveDevice();
    const deviceId = device?.id;

    // Check entity registry if available: the server device first, then the
    // devices under it (e.g. the Docker device's Container Updates Available)
    if (this.hass.entities && deviceId) {
      const serverDeviceIds = this.getServerDeviceIds(deviceId);
      for (const onServer of [true, false]) {
        for (const ent of Object.values(this.hass.entities)) {
          if (
            ent.device_id &&
            (onServer
              ? ent.device_id === deviceId
              : serverDeviceIds.has(ent.device_id)) &&
            ent.translation_key === translationKey &&
            (!domain || ent.entity_id.startsWith(`${domain}.`))
          ) {
            const stateObj = this.agentStates[ent.entity_id];
            if (stateObj) return stateObj;
          }
        }
      }
    }

    // Fallback: search states by naming patterns
    const states = Object.values(this.agentStates);
    return states.find((s) => {
      if (domain && !s.entity_id.startsWith(`${domain}.`)) return false;
      if (this.hass?.entities) {
        const reg = this.hass.entities[s.entity_id];
        if (
          reg &&
          reg.platform !== "unraid_management_agent"
        )
          return false;
      }
      const objectId = s.entity_id.split(".")[1] || "";
      const keyMatch =
        objectId.endsWith(`_${translationKey}`) ||
        objectId === translationKey ||
        (translationKey === "uptime" &&
          (objectId.endsWith("_up_since") || objectId === "up_since")) ||
        (translationKey === "network_interface_ip" &&
          objectId.includes("_network_") &&
          (objectId.endsWith("_ip") || objectId.endsWith("_ip_address")));

      if (device?.name) {
        const cleanName = this.slugifyDeviceName(device.name);
        return keyMatch && objectId.includes(cleanName);
      }
      return keyMatch;
    });
  }

  /**
   * Get all network interface metrics for active server.
   */
  protected getNetworkInterfaces(): Array<{
    name: string;
    displayName: string;
    ip?: HassEntity;
    speed?: HassEntity;
    rx?: HassEntity;
    tx?: HassEntity;
    link?: HassEntity;
  }> {
    if (!this.hass?.states) return [];
    const device = this.getActiveDevice();
    const cleanName = device?.name
      ? this.slugifyDeviceName(device.name)
      : undefined;

    const ifaceMap = new Map<
      string,
      {
        name: string;
        displayName: string;
        ip?: HassEntity;
        speed?: HassEntity;
        rx?: HassEntity;
        tx?: HassEntity;
        link?: HassEntity;
      }
    >();

    for (const [entityId, stateObj] of Object.entries(this.agentStates)) {
      if (cleanName && !entityId.includes(cleanName)) continue;
      // Interface entities live on the server device itself. Entities of its
      // child devices (e.g. a "Network card (41:00)" NIC device) can also
      // contain "_network_", so skip any entity registered to another device.
      const deviceId = this.hass.entities?.[entityId]?.device_id;
      if (device?.id && deviceId && deviceId !== device.id) continue;

      if (entityId.startsWith("binary_sensor.") && entityId.includes("_network_")) {
        if (entityId.includes("_network_service_")) continue;
        const linkMatch = entityId.match(
          /_network_(?:([a-zA-Z0-9_-]+)_link|([a-zA-Z0-9_-]+))$/i
        );
        const ifaceName = linkMatch ? linkMatch[1] || linkMatch[2] : null;
        if (ifaceName) {
          if (!ifaceMap.has(ifaceName)) {
            ifaceMap.set(ifaceName, {
              name: ifaceName,
              displayName: ifaceName.toUpperCase(),
            });
          }
          ifaceMap.get(ifaceName)!.link = stateObj;
          continue;
        }
      }

      const match = entityId.match(
        /_network_([a-zA-Z0-9_-]+)_(inbound(?:_throughput)?|outbound(?:_throughput)?|rx(?:_throughput)?|tx(?:_throughput)?|speed|ip|ip_address|link)$/i
      );
      if (!match || !match[1] || !match[2]) continue;
      const ifaceName = match[1];
      const prop = match[2].toLowerCase();

      if (!ifaceMap.has(ifaceName)) {
        ifaceMap.set(ifaceName, {
          name: ifaceName,
          displayName: ifaceName.toUpperCase(),
        });
      }
      const entry = ifaceMap.get(ifaceName)!;
      if (prop.startsWith("inbound") || prop.startsWith("rx")) entry.rx = stateObj;
      else if (prop.startsWith("outbound") || prop.startsWith("tx")) entry.tx = stateObj;
      else if (prop === "speed") entry.speed = stateObj;
      else if (prop === "ip" || prop === "ip_address") entry.ip = stateObj;
      else if (prop === "link") entry.link = stateObj;
    }

    return Array.from(ifaceMap.values()).sort((a, b) =>
      a.name.localeCompare(b.name, undefined, { numeric: true })
    );
  }

  /**
   * Get boot/flash disk usage entity if present.
   */
  protected getBootDiskEntity(): HassEntity | undefined {
    if (!this.hass?.states) return undefined;
    const device = this.getActiveDevice();
    const cleanName = device?.name
      ? this.slugifyDeviceName(device.name)
      : undefined;

    return Object.values(this.agentStates).find((s) => {
      if (!s.entity_id.startsWith("sensor.")) return false;
      if (cleanName && !s.entity_id.includes(cleanName)) return false;
      return (
        (s.entity_id.includes("_disk_flash_") ||
          s.entity_id.includes("_disk_boot_") ||
          s.entity_id.endsWith("_flash_usage") ||
          s.entity_id.endsWith("_boot_usage")) &&
        s.entity_id.endsWith("_usage")
      );
    });
  }

  /**
   * Find all entities matching a translation key (e.g. disks, docker containers).
   */
  protected getEntities(
    translationKey: string,
    domain?: string
  ): HassEntity[] {
    if (!this.hass?.states) return [];
    const device = this.getActiveDevice();
    const deviceId = device?.id;

    if (this.hass.entities && deviceId) {
      // Containers and VMs may be on their own devices under the server
      const serverDeviceIds = this.getServerDeviceIds(deviceId);
      const matches: HassEntity[] = [];
      for (const ent of Object.values(this.hass.entities)) {
        const keyMatch =
          ent.translation_key === translationKey ||
          (translationKey === "docker_container" &&
            (ent.translation_key === "container" ||
              ent.translation_key === "container_device_running")) ||
          (translationKey === "docker_container_autostart" &&
            (ent.translation_key === "container_autostart" ||
              ent.translation_key === "container_device_autostart")) ||
          (translationKey === "docker_container_restart" &&
            (ent.translation_key === "container_restart" ||
              ent.translation_key === "container_device_restart")) ||
          (translationKey === "virtual_machine" &&
            (ent.translation_key === "vm" || ent.translation_key === "vm_power")) ||
          (translationKey === "virtual_machine_status" &&
            ent.translation_key === "vm_status") ||
          (translationKey === "vm_reboot" &&
            (ent.translation_key === "vm_restart" || ent.translation_key === "vm_reboot"));

        if (
          ent.device_id &&
          serverDeviceIds.has(ent.device_id) &&
          keyMatch &&
          (!domain || ent.entity_id.startsWith(`${domain}.`))
        ) {
          const stateObj = this.agentStates[ent.entity_id];
          if (stateObj) matches.push(stateObj);
        }
      }
      if (matches.length > 0) return matches;
    }

    // Fallback to name pattern
    const cleanName = device?.name
      ? this.slugifyDeviceName(device.name)
      : undefined;

    const matchesTranslation = (s: HassEntity) => {
      if (this.hass?.entities) {
        const reg = this.hass.entities[s.entity_id];
        if (
          reg &&
          reg.platform !== "unraid_management_agent"
        )
          return false;
      }
      if (
        translationKey === "docker_container" ||
        translationKey === "container"
      ) {
        return (
          s.entity_id.startsWith("switch.") &&
          (s.entity_id.includes("_container_") ||
            s.entity_id.includes("_docker_")) &&
          !s.entity_id.includes("_autostart")
        );
      }
      if (
        translationKey === "docker_container_autostart" ||
        translationKey === "container_autostart"
      ) {
        return (
          s.entity_id.startsWith("switch.") &&
          (s.entity_id.includes("_container_") ||
            s.entity_id.includes("_docker_")) &&
          s.entity_id.includes("_autostart")
        );
      }
      if (
        translationKey === "docker_container_restart" ||
        translationKey === "container_restart"
      ) {
        return (
          s.entity_id.startsWith("button.") &&
          (s.entity_id.includes("_container_") ||
            s.entity_id.includes("_docker_")) &&
          (s.entity_id.includes("_restart") || s.entity_id.includes("_reboot"))
        );
      }
      if (
        translationKey === "virtual_machine" ||
        translationKey === "vm"
      ) {
        return (
          s.entity_id.startsWith("switch.") &&
          (s.entity_id.includes("_vm_") ||
            s.entity_id.includes("_virtual_machine_"))
        );
      }
      if (
        translationKey === "virtual_machine_status" ||
        translationKey === "vm_status"
      ) {
        return (
          s.entity_id.startsWith("sensor.") &&
          (s.entity_id.includes("_vm_") ||
            s.entity_id.includes("_virtual_machine_")) &&
          s.entity_id.endsWith("_status")
        );
      }
      if (
        translationKey === "vm_reboot" ||
        translationKey === "vm_restart"
      ) {
        return (
          s.entity_id.startsWith("button.") &&
          (s.entity_id.includes("_vm_") ||
            s.entity_id.includes("_virtual_machine_")) &&
          (s.entity_id.includes("_restart") || s.entity_id.includes("_reboot"))
        );
      }
      if (translationKey === "disk_usage") {
        return (
          (s.entity_id.includes("_disk_") ||
            s.entity_id.includes("_cache") ||
            s.entity_id.includes("_parity") ||
            s.entity_id.includes("_boot") ||
            s.entity_id.includes("_flash")) &&
          s.entity_id.endsWith("_usage") &&
          !s.entity_id.includes("_array_usage") &&
          !s.entity_id.includes("_share_")
        );
      }
      if (translationKey === "disk_temperature") {
        return (
          (s.entity_id.includes("_disk_") ||
            s.entity_id.includes("_cache") ||
            s.entity_id.includes("_parity") ||
            s.entity_id.includes("_boot")) &&
          (s.entity_id.endsWith("_temperature") || s.entity_id.includes("_temp"))
        );
      }
      if (translationKey === "disk_spin") {
        return (
          (s.entity_id.includes("_disk_") ||
            s.entity_id.includes("_cache") ||
            s.entity_id.includes("_parity")) &&
          s.entity_id.includes("_spin")
        );
      }
      if (translationKey === "disk_health") {
        return (
          (s.entity_id.includes("_disk_") ||
            s.entity_id.includes("_cache") ||
            s.entity_id.includes("_parity") ||
            s.entity_id.includes("_boot")) &&
          (s.entity_id.endsWith("_health") || s.entity_id.includes("_health_"))
        );
      }
      if (translationKey === "share_usage" || translationKey === "share") {
        return (
          s.entity_id.includes("_share_") &&
          s.entity_id.endsWith("_usage")
        );
      }
      const objectId = s.entity_id.split(".")[1] || "";
      return (
        objectId === translationKey ||
        objectId.endsWith(`_${translationKey}`) ||
        objectId.includes(`_${translationKey}_`) ||
        objectId.startsWith(`${translationKey}_`)
      );
    };

    const states = Object.values(this.agentStates);
    const domainStates = domain
      ? states.filter((s) => s.entity_id.startsWith(`${domain}.`))
      : states;

    if (cleanName) {
      return domainStates.filter(
        (s) => s.entity_id.includes(cleanName) && matchesTranslation(s)
      );
    }

    return domainStates.filter((s) => matchesTranslation(s));
  }

  /**
   * Find an entity by exact or regex pattern
   */
  protected findEntity(pattern: RegExp | string): HassEntity | undefined {
    if (!this.hass?.states) return undefined;
    if (typeof pattern === "string") {
      return this.agentStates[pattern];
    }
    return Object.values(this.agentStates).find((s) =>
      pattern.test(s.entity_id)
    );
  }

  /** Toggle switch service call */
  protected async toggleEntity(entityId: string): Promise<void> {
    if (!this.hass || !this.agentStates[entityId]) return;
    const domain = entityId.split(".")[0] || "homeassistant";
    await this.hass.callService(domain, "toggle", { entity_id: entityId });
  }

  /** Press button service call */
  protected async pressButton(entityId: string): Promise<void> {
    if (!this.hass || !this.agentStates[entityId]) return;
    await this.hass.callService("button", "press", { entity_id: entityId });
  }

  /** Open more info popup */
  protected openMoreInfo(entityId: string): void {
    fireEvent(this, "hass-more-info", { entityId });
  }

  /** Navigate to a path or subview */
  protected navigate(path: string, replace = false): void {
    if (!path) return;
    if (replace) {
      window.history.replaceState(null, "", path);
    } else {
      window.history.pushState(null, "", path);
    }
    fireEvent(window, "location-changed", { replace });
  }

  protected renderHeader(
    title: string,
    subtitle: string,
    iconPath: string,
    badgeContent?: TemplateResult
  ): TemplateResult | typeof nothing {
    if (this.config.embedded || this.config.hide_header) {
      return nothing;
    }
    return html`
      <div class="header">
        <div class="header-main">
          <div class="header-icon">${iconTemplate(iconPath, 22)}</div>
          <div class="header-titles">
            <span class="header-title">${title}</span>
            <span class="header-subtitle">${subtitle}</span>
          </div>
        </div>
        ${badgeContent ? html`<div class="header-actions">${badgeContent}</div>` : ""}
      </div>
    `;
  }
}
