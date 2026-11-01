import { html, nothing, type TemplateResult } from "lit";
import {
  SERVER_CARD_TAG,
  SERVER_EDITOR_TAG,
} from "./config";
import { BaseUnraidCard, formatDataRate } from "./dashboard-cards-base";
import { UnraidServerCardEditor } from "./dashboard-cards-editor";
import {
  iconTemplate,
  mdiAlertCircle,
  mdiServer,
} from "./icons";
import { registerDashboardCard } from "./register-dashboard-card";

export class UnraidServerCard extends BaseUnraidCard {
  static override editorTag = SERVER_EDITOR_TAG;

  private formatUptime(secondsOrIso: string | undefined): string {
    if (!secondsOrIso) return "Unknown";
    const trimmed = secondsOrIso.trim();
    let totalSec = 0;
    if (/^\d+(\.\d+)?$/.test(trimmed)) {
      totalSec = Math.floor(Number(trimmed));
    } else {
      const date = new Date(secondsOrIso);
      if (!isNaN(date.getTime())) {
        totalSec = Math.max(0, Math.floor((Date.now() - date.getTime()) / 1000));
      } else {
        return secondsOrIso;
      }
    }

    const days = Math.floor(totalSec / 86400);
    const hours = Math.floor((totalSec % 86400) / 3600);
    const mins = Math.floor((totalSec % 3600) / 60);

    if (days > 0) return `${days}d ${hours}h`;
    if (hours > 0) return `${hours}h ${mins}m`;
    return `${mins}m`;
  }

  protected override render(): TemplateResult {
    const device = this.getActiveDevice();
    const serverName = this.config.title || device?.name_by_user || device?.name || "Unraid Server";

    // Entities
    const cpuState = this.getEntity("cpu_usage");
    const ramState = this.getEntity("ram_usage");
    const arrayUsage = this.getEntity("array_usage");
    const arrayState = this.getEntity("array_state");
    const arrayStarted = this.getEntity("array_started", "binary_sensor");
    const tempState =
      this.getEntity("system_temperature") ||
      this.getEntity("temperature_average") ||
      this.getEntity("cpu_temperature");
    const powerState = this.getEntity("cpu_power");
    const uptimeState = this.getEntity("uptime");
    const alertsState = this.getEntity("notifications_unread_alert");
    const ipState = this.getEntity("network_interface_ip");

    const cpuPct = Math.round(Number(cpuState?.state) || 0);
    const ramPct = Math.round(Number(ramState?.state) || 0);
    const arrayPct = Math.round(Number(arrayUsage?.state) || 0);

    const arrayStateNorm = arrayState?.state?.toLowerCase().trim();
    const isArrayStarted = arrayStarted
      ? arrayStarted.state === "on"
      : arrayStateNorm === "started" || arrayStateNorm === "normal";
    const alertCount = Number(alertsState?.state) || 0;

    const cpuModel = (cpuState?.attributes?.cpu_model as string) || (device?.model ?? "Multi-Core CPU");
    const ramUsedStr = (ramState?.attributes?.used as string) || "";
    const ramTotalStr = (ramState?.attributes?.total as string) || "";
    const arrayUsedStr = (arrayUsage?.attributes?.capacity_used as string) || "";
    const arrayTotalStr = (arrayUsage?.attributes?.capacity_total as string) || "";

    // Network interfaces and primary interface
    const ifaces = this.getNetworkInterfaces();
    const primaryIface = ifaces.length > 0 ? ifaces[0] : undefined;
    const speedRaw = primaryIface?.speed?.state || (primaryIface?.link?.attributes?.speed_mbps as string | number | undefined) || (primaryIface?.rx?.attributes?.network_speed as number | undefined);
    const netSpeedNum = speedRaw != null ? Number(speedRaw) : undefined;
    const netSpeedText = netSpeedNum
      ? netSpeedNum >= 1000
        ? `${netSpeedNum / 1000} Gbps`
        : `${netSpeedNum} Mbps`
      : "";

    const rxRate = formatDataRate(primaryIface?.rx);
    const txRate = formatDataRate(primaryIface?.tx);
    const rxText = rxRate === "--" ? "" : rxRate;
    const txText = txRate === "--" ? "" : txRate;
    const netTrafficText = rxText && txText ? `↓ ${rxText} • ↑ ${txText}` : netSpeedText || "Active";

    // Boot / Flash device
    const bootDisk = this.getBootDiskEntity();
    const bootAttrs = bootDisk?.attributes;
    const bootUsed = (bootAttrs?.used || bootAttrs?.used_size || bootAttrs?.fs_used) as string | undefined;
    const bootTotal = (bootAttrs?.total || bootAttrs?.total_size || bootAttrs?.fs_size) as string | undefined;
    const bootDevice = (bootAttrs?.device || bootAttrs?.vendor) as string | undefined;
    const bootText = bootUsed && bootTotal
      ? `Flash (${bootUsed} / ${bootTotal})`
      : bootDevice
      ? `Flash (${bootDevice})`
      : "Flash (USB)";
    const bootTooltip = bootAttrs?.filesystem ? `Device: ${bootDevice || "USB"} • FS: ${bootAttrs.filesystem}` : "USB Flash Boot Drive";

    const badge = html`
      <span class="badge ${isArrayStarted ? "badge-online" : "badge-error"}">
        <span class="pulse-dot"></span>
        <span>Array ${arrayState?.state || (isArrayStarted ? "Started" : "Stopped")}</span>
      </span>
      ${alertCount > 0
        ? html`
            <span class="badge badge-error">
              ${iconTemplate(mdiAlertCircle, 13)}
              <span>${alertCount}</span>
            </span>
          `
        : nothing}
    `;

    return html`
      <ha-card>
        <div class="card-content">
        ${this.renderHeader(
          serverName,
          `${device?.model || "Unraid OS"} • Up ${this.formatUptime(uptimeState?.state)}`,
          mdiServer,
          badge
        )}
        <div class="rings-grid">
          <button
            type="button"
            ?disabled=${!(cpuState)}
            class="interactive ring-card"
            @click=${() => cpuState && this.openMoreInfo(cpuState.entity_id)}
            title="Click to view CPU details"
          >
            <span data-block
              class="ring-gauge"
              style="--pct: ${cpuPct}; --ring-color: ${cpuPct > 80 ? "var(--unraid-error)" : cpuPct > 50 ? "var(--unraid-warning)" : "var(--unraid-online)"}"
            >
              <span class="ring-content ltr-value">${cpuPct}%</span>
            </span>
            <span class="ring-label">CPU Load</span>
            <span class="ring-subtext">
              ${tempState?.state ? `${tempState.state}°C` : ""}${powerState?.state ? ` • ${powerState.state}W` : ""}
            </span>
          </button>
          <button
            type="button"
            ?disabled=${!(ramState)}
            class="interactive ring-card"
            @click=${() => ramState && this.openMoreInfo(ramState.entity_id)}
            title="Click to view Memory details"
          >
            <span data-block
              class="ring-gauge"
              style="--pct: ${ramPct}; --ring-color: ${ramPct > 85 ? "var(--unraid-error)" : "var(--unraid-info)"}"
            >
              <span class="ring-content ltr-value">${ramPct}%</span>
            </span>
            <span class="ring-label">Memory</span>
            <span class="ring-subtext">${ramUsedStr && ramTotalStr ? `${ramUsedStr} / ${ramTotalStr}` : `${ramPct}% used`}</span>
          </button>
          <button
            type="button"
            ?disabled=${!(arrayUsage)}
            class="interactive ring-card"
            @click=${() => arrayUsage && this.openMoreInfo(arrayUsage.entity_id)}
            title="Click to view Array storage details"
          >
            <span data-block
              class="ring-gauge"
              style="--pct: ${arrayPct}; --ring-color: var(--unraid-accent)"
            >
              <span class="ring-content ltr-value">${arrayPct}%</span>
            </span>
            <span class="ring-label">Array Storage</span>
            <span class="ring-subtext">${arrayUsedStr && arrayTotalStr ? `${arrayUsedStr} / ${arrayTotalStr}` : `${arrayPct}% used`}</span>
          </button>
        </div>

        ${this.config.show_system_info !== false
          ? html`
              <div class="divider"></div>
              <div class="detail-grid">
                <div class="detail-item">
                  <span class="detail-label">Processor</span>
                  <span class="detail-val" title="${cpuModel}">${cpuModel}</span>
                </div>
                <div class="detail-item">
                  <span class="detail-label">OS Version</span>
                  <span class="detail-val ltr-value">${device?.sw_version || "Unraid OS"}</span>
                </div>
                <button
                  type="button"
                  ?disabled=${!(uptimeState)}
                  class="interactive detail-item"
                  @click=${() => uptimeState && this.openMoreInfo(uptimeState.entity_id)}
                  title="Click to view Uptime details"
                >
                  <span class="detail-label">System Uptime</span>
                  <span class="detail-val">${this.formatUptime(uptimeState?.state)}</span>
                </button>
                <button
                  type="button"
                  ?disabled=${!(primaryIface?.rx || ipState)}
                  class="interactive detail-item"
                  @click=${() => (primaryIface?.rx ? this.openMoreInfo(primaryIface.rx.entity_id) : ipState && this.openMoreInfo(ipState.entity_id))}
                  title="Click to view Network details"
                >
                  <span class="detail-label">Primary Network</span>
                  <span class="detail-val ltr-value" title="${primaryIface ? `${primaryIface.name} • ${netSpeedText}` : 'Connected'}">
                    ${primaryIface ? `${primaryIface.name}: ` : ""}${primaryIface?.ip?.state || ipState?.state || "Connected"}
                  </span>
                </button>
                <button
                  type="button"
                  ?disabled=${!(primaryIface?.rx || primaryIface?.speed)}
                  class="interactive detail-item"
                  @click=${() => (primaryIface?.rx ? this.openMoreInfo(primaryIface.rx.entity_id) : primaryIface?.speed && this.openMoreInfo(primaryIface.speed.entity_id))}
                  title="Click to view Network traffic details"
                >
                  <span class="detail-label">Network Traffic</span>
                  <span class="detail-val ltr-value" title="${netSpeedText ? `Link Speed: ${netSpeedText}` : 'Network Speed'}">${netTrafficText}</span>
                </button>
                <button
                  type="button"
                  ?disabled=${!(bootDisk)}
                  class="interactive detail-item"
                  @click=${() => bootDisk && this.openMoreInfo(bootDisk.entity_id)}
                  title="Click to view Boot device details"
                >
                  <span class="detail-label">Boot Device</span>
                  <span class="detail-val" title="${bootTooltip}">${bootText}</span>
                </button>
                <button
                  type="button"
                  ?disabled=${!(alertsState)}
                  class="interactive detail-item"
                  @click=${() => alertsState && this.openMoreInfo(alertsState.entity_id)}
                  title="Click to view Notifications"
                >
                  <span class="detail-label">System Health</span>
                  <span class="detail-val" style="color: ${alertCount === 0 ? "var(--unraid-online)" : "var(--unraid-error)"}">
                    ${alertCount === 0 ? "Normal • Healthy" : `${alertCount} Active Alerts`}
                  </span>
                </button>
              </div>
            `
          : nothing}
      </div>
      </ha-card>
    `;
  }
}

registerDashboardCard({
  tag: SERVER_CARD_TAG,
  editorTag: SERVER_EDITOR_TAG,
  card: UnraidServerCard,
  editor: UnraidServerCardEditor,
  name: "Unraid Server Overview Card",
  description: "Server metrics, CPU/RAM ring gauges, and hardware health.",
});
