import { html, nothing, type TemplateResult } from "lit";
import {
  NETWORK_CARD_TAG,
  NETWORK_EDITOR_TAG,
} from "./config";
import { BaseUnraidCard, formatDataRate } from "./dashboard-cards-base";
import { UnraidNetworkCardEditor } from "./dashboard-cards-editor";
import { fireEvent } from "./ha-types";
import {
  iconTemplate,
  mdiDownload,
  mdiEthernet,
  mdiLanConnect,
  mdiUpload,
} from "./icons";
import { registerDashboardCard } from "./register-dashboard-card";

export class UnraidNetworkCard extends BaseUnraidCard {
  static override editorTag = NETWORK_EDITOR_TAG;

  private isValidIp(s?: string): boolean {
    return (
      Boolean(s) &&
      !["unavailable", "unknown", "none", "--"].includes(s!.toLowerCase().trim())
    );
  }

  private formatSpeed(speedStr?: string): string {
    if (!speedStr) return "";
    const clean = speedStr.toLowerCase().trim();
    if (["unavailable", "unknown", "none", "--"].includes(clean)) return "";
    const num = Number(speedStr);
    if (isNaN(num)) return speedStr;
    if (num >= 1000) return `${num / 1000} Gbps`;
    return `${num} Mbps`;
  }

  private handleMoreInfo(entityId?: string): void {
    if (!entityId) return;
    fireEvent(this, "hass-more-info", { entityId });
  }

  private sanitizeHttpUrl(url: unknown): string | undefined {
    if (typeof url !== "string" || !url.trim()) return undefined;
    try {
      const parsed = new URL(url);
      if (parsed.protocol === "http:" || parsed.protocol === "https:") {
        return parsed.toString();
      }
    } catch {
      // not a valid absolute URL
    }
    return undefined;
  }

  protected override render(): TemplateResult {
    const device = this.getActiveDevice();
    const serverName =
      this.config.title ||
      device?.name_by_user ||
      device?.name ||
      "Unraid Server";

    const ifaces = this.getNetworkInterfaces();
    const networkAccess = this.getEntity("network_access");
    const accessAttrs = networkAccess?.attributes;
    const lanUrl =
      this.sanitizeHttpUrl(accessAttrs?.LAN_IPv4_ipv4) ||
      this.sanitizeHttpUrl(networkAccess?.state);
    const fqdnUrl = this.sanitizeHttpUrl(accessAttrs?.FQDN_LAN_ipv4);

    const connectedCount = ifaces.filter(
      (i) => i.link?.state === "on" || this.isValidIp(i.ip?.state)
    ).length;

    const badge = html`
      <span class="badge ${connectedCount > 0 ? "badge-online" : "badge-error"}">
        <span class="pulse-dot"></span>
        <span>${connectedCount} Connected</span>
      </span>
    `;

    return html`
      <ha-card>
        <div class="uma-card-content">
        ${this.renderHeader(
          this.config.title || `${serverName} Network`,
          `${device?.model || "Unraid"} • ${ifaces.length} Interface${ifaces.length === 1 ? "" : "s"}`,
          mdiLanConnect,
          badge
        )}
        <div class="item-list">
          ${ifaces.length > 0
            ? ifaces.map((iface) => {
                const isConnected =
                  iface.link?.state === "on" || this.isValidIp(iface.ip?.state);
                const attrIp = iface.rx?.attributes?.network_ip as string | undefined;
                const ipStr = this.isValidIp(iface.ip?.state) ? iface.ip!.state : this.isValidIp(attrIp) ? attrIp! : "--";
                const macStr = (iface.ip?.attributes?.mac_address as string) || (iface.link?.attributes?.mac_address as string) || "";
                const mtu = (iface.link?.attributes?.mtu as number) || (iface.ip?.attributes?.mtu as number) || undefined;
                const speedVal = iface.speed?.state || (iface.link?.attributes?.speed_mbps as string | number | undefined) || (iface.rx?.attributes?.network_speed as number | undefined);
                const speedText = this.formatSpeed(speedVal != null ? String(speedVal) : undefined);

                const rxRate = formatDataRate(iface.rx);
                const txRate = formatDataRate(iface.tx);
                const totalRx = (iface.rx?.attributes?.total_received as string) || "";
                const totalTx = (iface.tx?.attributes?.total_sent as string) || "";

                const primaryEntityId =
                  iface.ip?.entity_id ||
                  iface.rx?.entity_id ||
                  iface.link?.entity_id;

                return html`
                  <button
                    type="button"
                    class="interactive list-row network-row"
                    style="flex-direction: column; align-items: stretch; gap: var(--ha-space-2, 8px); padding: var(--ha-space-3, 12px) var(--ha-space-3, 12px);"
                    title="Click for details on ${iface.name}"
                    @click=${() => this.handleMoreInfo(primaryEntityId)}
                  >
                    <span data-block style="display: flex; flex-wrap: wrap; gap: var(--ha-space-1, 4px); align-items: center; justify-content: space-between;">
                      <span data-block class="row-left" style="gap: var(--ha-space-2, 8px);">
                        <span class="badge ${isConnected ? "badge-online" : "badge-error"}" style="min-width: 50px; justify-content: center;">
                          ${iconTemplate(mdiEthernet, 13)}
                          <span class="ltr-value">${iface.name}</span>
                        </span>
                        <span class="ltr-value" style="font-weight: var(--ha-font-weight-bold, 600); font-size: var(--ha-font-size-m, 14px);">
                          ${ipStr}
                        </span>
                      </span>

                      <span data-block class="row-right" style="gap: var(--ha-space-2, 8px);">
                        ${speedText
                          ? html`
                              <span
                                class="badge ltr-value"
                                style="color: var(--unraid-info); background: color-mix(in srgb, var(--unraid-info) 12%, transparent); font-weight: var(--ha-font-weight-bold, 600); font-size: var(--ha-font-size-s, 12px);"
                              >
                                ${speedText}
                              </span>
                            `
                          : nothing}
                        <span
                          class="badge ${isConnected ? "badge-online" : "badge-standby"}"
                          style="font-size: var(--ha-font-size-s, 12px);"
                        >
                          ${isConnected ? "Up" : "Down"}
                        </span>
                      </span>
                    </span>
                    <span data-block style="display: flex; flex-wrap: wrap; gap: var(--ha-space-1, 4px); align-items: center; justify-content: space-between; font-size: var(--ha-font-size-s, 12px); color: var(--unraid-subtext); border-block-start: 1px solid var(--unraid-border); padding-block-start: var(--ha-space-2, 8px);">
                      <span data-block style="display: flex; align-items: center; gap: var(--ha-space-3, 12px);">
                        <span style="display: flex; align-items: center; gap: var(--ha-space-1, 4px);" title="${totalRx ? `Total Inbound: ${totalRx}` : 'Inbound Transfer Rate'}">
                          <span style="color: var(--unraid-online);">${iconTemplate(mdiDownload, 13)}</span>
                          <span class="ltr-value" style="font-family: var(--ha-font-family-code, monospace); font-weight: var(--ha-font-weight-medium, 500);">${rxRate}</span>
                          ${totalRx ? html`<span class="ltr-value" style="opacity: 0.7; font-size: var(--ha-font-size-s, 12px);">(${totalRx})</span>` : nothing}
                        </span>

                        <span style="display: flex; align-items: center; gap: var(--ha-space-1, 4px);" title="${totalTx ? `Total Outbound: ${totalTx}` : 'Outbound Transfer Rate'}">
                          <span style="color: var(--unraid-info);">${iconTemplate(mdiUpload, 13)}</span>
                          <span class="ltr-value" style="font-family: var(--ha-font-family-code, monospace); font-weight: var(--ha-font-weight-medium, 500);">${txRate}</span>
                          ${totalTx ? html`<span class="ltr-value" style="opacity: 0.7; font-size: var(--ha-font-size-s, 12px);">(${totalTx})</span>` : nothing}
                        </span>
                      </span>

                      <span data-block style="display: flex; align-items: center; gap: var(--ha-space-2, 8px); opacity: 0.8; font-size: var(--ha-font-size-s, 12px);">
                        ${mtu ? html`<span class="ltr-value">MTU ${mtu}</span>` : nothing}
                        ${macStr ? html`<span class="ltr-value" style="font-family: var(--ha-font-family-code, monospace);">${macStr}</span>` : nothing}
                      </span>
                    </span>
                  </button>
                `;
              })
            : html`
                <div class="empty-state">
                  No network interfaces discovered for this server.
                </div>
              `}
        </div>

        ${lanUrl || fqdnUrl
          ? html`
              <div class="divider"></div>
              <div class="detail-grid">
                ${lanUrl
                  ? html`
                      <div class="detail-item">
                        <span class="detail-label">LAN WebGUI</span>
                        <a
                          href="${lanUrl}"
                          target="_blank"
                          rel="noreferrer"
                          class="detail-val ltr-value"
                          style="color: var(--unraid-accent); text-decoration: none;"
                        >
                          ${lanUrl}
                        </a>
                      </div>
                    `
                  : nothing}
                ${fqdnUrl
                  ? html`
                      <div class="detail-item">
                        <span class="detail-label">Remote Access URL</span>
                        <a
                          href="${fqdnUrl}"
                          target="_blank"
                          rel="noreferrer"
                          class="detail-val ltr-value"
                          style="color: var(--unraid-info); text-decoration: none;"
                        >
                          Connect FQDN
                        </a>
                      </div>
                    `
                  : nothing}
              </div>
            `
          : nothing}
      </div>
      </ha-card>
    `;
  }
}

registerDashboardCard({
  tag: NETWORK_CARD_TAG,
  editorTag: NETWORK_EDITOR_TAG,
  card: UnraidNetworkCard,
  editor: UnraidNetworkCardEditor,
  name: "Unraid Network Card",
  description: "Network interfaces, link speeds, live throughput, and IP addresses.",
});
