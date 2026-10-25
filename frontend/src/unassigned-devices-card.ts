import { html, nothing, type TemplateResult } from "lit";
import {
  UNASSIGNED_DEVICES_CARD_TAG,
  UNASSIGNED_DEVICES_EDITOR_TAG,
} from "./config";
import { BaseUnraidCard } from "./dashboard-cards-base";
import { UnraidUnassignedDevicesCardEditor } from "./dashboard-cards-editor";
import {
  iconTemplate,
  mdiHarddisk,
  mdiHarddiskPlus,
} from "./icons";
import { registerDashboardCard } from "./register-dashboard-card";

interface UnassignedDeviceItem {
  id: string;
  name: string;
  size?: string;
  usagePct?: number;
  isMounted: boolean;
  temp?: string;
  fsType?: string;
  sizeEntityId?: string;
  mountedEntityId?: string;
}

export class UnraidUnassignedDevicesCard extends BaseUnraidCard {
  static override editorTag = UNASSIGNED_DEVICES_EDITOR_TAG;

  private getDevices(): UnassignedDeviceItem[] {
    const devMap = new Map<string, UnassignedDeviceItem>();
    if (!this.hass?.states) return [];

    const device = this.getActiveDevice();
    const deviceId = device?.id;

    for (const [entityId, stateObj] of Object.entries(this.agentStates)) {
      if (deviceId && this.hass.entities) {
        const ent = this.hass.entities[entityId];
        if (ent && ent.device_id && ent.device_id !== deviceId) continue;
      }

      const match = entityId.match(/_unassigned_device_([a-zA-Z0-9_-]+)_(size|usage|mounted|temperature|temp)$/i);
      if (!match || !match[1] || !match[2]) continue;

      const devKey = match[1].toLowerCase();
      const rawName = (stateObj.attributes?.friendly_name as string) || match[1] || "Unassigned Device";
      const cleanName = rawName
        .replace(/^(?:.*?\s+)?Unassigned Device\s+/i, "")
        .replace(/\s+(?:size|usage|mounted|temperature|temp)$/i, "")
        .trim();

      if (!devMap.has(devKey)) {
        devMap.set(devKey, {
          id: match[1],
          name: cleanName,
          isMounted: false,
        });
      }

      const item = devMap.get(devKey)!;
      const prop = match[2].toLowerCase();

      if (prop === "size") {
        item.sizeEntityId = entityId;
        item.size = `${stateObj.state} ${stateObj.attributes?.unit_of_measurement || ""}`.trim();
        item.fsType = stateObj.attributes?.filesystem as string;
      } else if (prop === "usage") {
        const num = parseFloat(stateObj.state);
        item.usagePct = !isNaN(num) ? Math.round(num) : undefined;
      } else if (prop === "mounted") {
        item.mountedEntityId = entityId;
        item.isMounted = stateObj.state === "on" || stateObj.state === "true";
      } else if (prop === "temperature" || prop === "temp") {
        item.temp = `${stateObj.state}°C`;
      }
    }

    return Array.from(devMap.values()).sort((a, b) => a.name.localeCompare(b.name));
  }

  protected override render(): TemplateResult {
    const device = this.getActiveDevice();
    const serverName = this.config.title || device?.name_by_user || device?.name || "Unraid Server";
    const devices = this.getDevices();

    return html`
      <ha-card>
        ${this.renderHeader(
          serverName,
          "Unassigned Storage Devices",
          mdiHarddiskPlus,
          html`
            <span class="badge ${devices.length > 0 ? "badge-online" : ""}">
              <span class="pulse-dot"></span>
              <span>${devices.length} Connected</span>
            </span>
          `
        )}

        ${devices.length === 0
          ? html`
              <div class="empty-state">
                ${iconTemplate(mdiHarddiskPlus, 32)}
                <div class="empty-title">No Unassigned Disks Found</div>
                <div class="empty-subtext">All connected disks are assigned to the array or pools.</div>
              </div>
            `
          : html`
              <div class="disk-list">
                ${devices.map((dev) => {
                  return html`
                    <div
                      class="disk-row"
                      @click=${() => (dev.sizeEntityId || dev.mountedEntityId) && this.openMoreInfo((dev.sizeEntityId || dev.mountedEntityId)!)}
                      style="cursor: pointer;"
                    >
                      <div class="disk-main">
                        <span class="disk-icon ${dev.isMounted ? "disk-online" : "disk-standby"}">
                          ${iconTemplate(mdiHarddisk, 18)}
                        </span>
                        <div class="disk-info">
                          <span class="disk-name">${dev.name}</span>
                          <span class="disk-subtext">
                            ${dev.size ? dev.size : "Disk"}
                            ${dev.fsType ? ` • ${dev.fsType}` : ""}
                            ${dev.temp ? ` • ${dev.temp}` : ""}
                          </span>
                        </div>
                      </div>
                      <div class="disk-meta">
                        ${dev.usagePct !== undefined ? html`<span class="disk-temp">${dev.usagePct}%</span>` : nothing}
                        <span class="badge ${dev.isMounted ? "badge-online" : ""}">
                          ${dev.isMounted ? "MOUNTED" : "UNMOUNTED"}
                        </span>
                      </div>
                    </div>
                  `;
                })}
              </div>
            `}
      </ha-card>
    `;
  }
}

registerDashboardCard({
  tag: UNASSIGNED_DEVICES_CARD_TAG,
  editorTag: UNASSIGNED_DEVICES_EDITOR_TAG,
  card: UnraidUnassignedDevicesCard,
  editor: UnraidUnassignedDevicesCardEditor,
  name: "Unraid Unassigned Devices Card",
  description: "Monitor unassigned storage drives, partitions, and external USB disks",
});
