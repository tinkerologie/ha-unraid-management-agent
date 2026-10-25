import { html, type TemplateResult } from "lit";
import {
  FANS_CARD_TAG,
  FANS_EDITOR_TAG,
} from "./config";
import { BaseUnraidCard } from "./dashboard-cards-base";
import { UnraidFansCardEditor } from "./dashboard-cards-editor";
import {
  iconTemplate,
  mdiAlertCircle,
  mdiFan,
} from "./icons";
import { registerDashboardCard } from "./register-dashboard-card";

interface FanItem {
  id: string;
  name: string;
  rpm: number;
  rpmText: string;
  isFailed: boolean;
  fanId?: number | string;
  controlEntityId?: string;
  rpmEntityId: string;
}

export class UnraidFansCard extends BaseUnraidCard {
  static override editorTag = FANS_EDITOR_TAG;

  private getFans(): FanItem[] {
    const list: FanItem[] = [];
    if (!this.hass?.states) return list;

    const device = this.getActiveDevice();
    const deviceId = device?.id;

    // Map control numbers
    const controlMap = new Map<string, string>();
    for (const [entityId, stateObj] of Object.entries(this.agentStates)) {
      if (entityId.startsWith("number.") && (entityId.includes("_fan_") || entityId.includes("fan_control"))) {
        if (deviceId && this.hass.entities) {
          const ent = this.hass.entities[entityId];
          // Fans of a USB controller sit on a child device of the server
          if (ent && ent.device_id && !this.isServerOrChildDevice(ent.device_id, deviceId)) {
            continue;
          }
        }
        const reg = this.hass.entities?.[entityId];
        if (reg && reg.platform !== "unraid_management_agent" && reg.platform !== "unraid") continue;
        const fanIdAttr = stateObj.attributes?.fan_id;
        if (fanIdAttr !== undefined) {
          controlMap.set(String(fanIdAttr), entityId);
        }
      }
    }

    for (const [entityId, stateObj] of Object.entries(this.agentStates)) {
      if (!entityId.startsWith("sensor.")) continue;

      // Check device ID or naming
      if (deviceId && this.hass.entities) {
        const ent = this.hass.entities[entityId];
        // Fans of a USB controller sit on a child device of the server
        if (ent && ent.device_id && !this.isServerOrChildDevice(ent.device_id, deviceId)) {
          continue;
        }
      }
      const reg = this.hass.entities?.[entityId];
      if (reg && reg.platform !== "unraid_management_agent" && reg.platform !== "unraid") continue;

      // Check fan sensor pattern
      const isFan =
        stateObj.attributes?.unit_of_measurement === "RPM" ||
        stateObj.attributes?.unit_of_measurement === "rpm" ||
        entityId.includes("_fan_") ||
        entityId.endsWith("_fan");

      if (!isFan) continue;

      const rpmNum = parseInt(stateObj.state, 10);
      const isFailed =
        stateObj.attributes?.is_failed === true ||
        stateObj.attributes?.status === "failed";
      const fanId = stateObj.attributes?.fan_id as string | number | undefined;
      const originalName =
        (stateObj.attributes?.original_name as string) ||
        (stateObj.attributes?.friendly_name as string) ||
        entityId.split(".")[1] ||
        "Fan";

      const cleanName = originalName
        .replace(/^(?:.*?\s+)?Fan\s+/i, "Fan ")
        .replace(/\s+RPM$/i, "")
        .replace(/\s+Speed$/i, "")
        .trim();

      list.push({
        id: entityId,
        name: cleanName,
        rpm: !isNaN(rpmNum) ? rpmNum : 0,
        rpmText: !isNaN(rpmNum) ? `${rpmNum} RPM` : stateObj.state,
        isFailed,
        fanId,
        controlEntityId: fanId !== undefined ? controlMap.get(String(fanId)) : undefined,
        rpmEntityId: entityId,
      });
    }

    // Fallback: If no sensor.* RPM entities exist, check for number.* fan controls (e.g. UMA fan speed controls)
    if (list.length === 0) {
      for (const [entityId, stateObj] of Object.entries(this.agentStates)) {
        if (!entityId.startsWith("number.")) continue;
        if (deviceId && this.hass.entities) {
          const ent = this.hass.entities[entityId];
          // Fans of a USB controller sit on a child device of the server
          if (ent && ent.device_id && !this.isServerOrChildDevice(ent.device_id, deviceId)) {
            continue;
          }
        }
        const reg = this.hass.entities?.[entityId];
        if (reg && reg.platform !== "unraid_management_agent" && reg.platform !== "unraid") continue;
        if (!entityId.includes("_fan_")) continue;

        const fanId = stateObj.attributes?.fan_id as string | number | undefined;
        const attrRpm = stateObj.attributes?.rpm != null ? Number(stateObj.attributes.rpm) : NaN;
        const speedVal = parseFloat(stateObj.state);
        const rpmNum = !isNaN(attrRpm) ? attrRpm : 0;
        const rpmText = !isNaN(attrRpm)
          ? `${attrRpm} RPM`
          : !isNaN(speedVal)
          ? `${Math.round(speedVal)}%`
          : stateObj.state;

        const originalName =
          (stateObj.attributes?.original_name as string) ||
          (stateObj.attributes?.friendly_name as string) ||
          entityId.split(".")[1] ||
          "Fan";

        const cleanName = originalName
          .replace(/^(?:.*?\s+)?Fan\s+/i, "Fan ")
          .replace(/\s+RPM$/i, "")
          .replace(/\s+Speed$/i, "")
          .trim();

        list.push({
          id: entityId,
          name: cleanName,
          rpm: rpmNum,
          rpmText,
          isFailed: false,
          fanId,
          controlEntityId: entityId,
          rpmEntityId: entityId,
        });
      }
    }

    return list.sort((a, b) => a.name.localeCompare(b.name, undefined, { numeric: true }));
  }

  protected override render(): TemplateResult {
    const device = this.getActiveDevice();
    const serverName = this.config.title || device?.name_by_user || device?.name || "Unraid Server";
    const fans = this.getFans();

    return html`
      <ha-card>
        ${this.renderHeader(
          serverName,
          "Cooling & Fans",
          mdiFan,
          html`
            <span class="badge ${fans.some((f) => f.isFailed) ? "badge-error" : "badge-online"}">
              <span class="pulse-dot"></span>
              <span>${fans.length} Fan${fans.length === 1 ? "" : "s"}</span>
            </span>
          `
        )}

        ${fans.length === 0
          ? html`
              <div class="empty-state">
                ${iconTemplate(mdiFan, 32)}
                <div class="empty-title">No Fan Sensors Found</div>
                <div class="empty-subtext">No cooling fans reported by system sensors or IPMI.</div>
              </div>
            `
          : html`
              <div class="disk-list">
                ${fans.map((f) => {
                  return html`
                    <div
                      class="disk-row"
                      @click=${() => this.openMoreInfo(f.controlEntityId || f.rpmEntityId)}
                      style="cursor: pointer;"
                      title="Click to view fan details / controls"
                    >
                      <div class="disk-main">
                        <span class="disk-icon ${f.isFailed ? "disk-warning" : "disk-online"}">
                          ${iconTemplate(f.isFailed ? mdiAlertCircle : mdiFan, 18)}
                        </span>
                        <div class="disk-info">
                          <span class="disk-name">${f.name}</span>
                          <span class="disk-subtext">
                            ${f.isFailed ? "Fan Fault Detected" : f.rpm > 0 ? "Operating Normally" : "Stopped / Idle"}
                          </span>
                        </div>
                      </div>
                      <div class="disk-meta">
                        <span class="disk-temp" style="color: ${f.isFailed ? "var(--unraid-error)" : f.rpm > 2000 ? "var(--unraid-warning)" : "var(--unraid-text)"};">
                          ${f.rpmText}
                        </span>
                        ${f.isFailed
                          ? html`<span class="badge badge-error">FAULT</span>`
                          : f.rpm > 0
                          ? html`<span class="badge badge-online">ACTIVE</span>`
                          : html`<span class="badge">OFF</span>`}
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
  tag: FANS_CARD_TAG,
  editorTag: FANS_EDITOR_TAG,
  card: UnraidFansCard,
  editor: UnraidFansCardEditor,
  name: "Unraid Fans Card",
  description: "Monitor system cooling fans, RPM speeds, and control statuses",
});
