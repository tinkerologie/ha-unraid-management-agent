import { html, nothing, type TemplateResult } from "lit";
import {
  REMOTE_SHARES_CARD_TAG,
  REMOTE_SHARES_EDITOR_TAG,
} from "./config";
import { BaseUnraidCard } from "./dashboard-cards-base";
import { UnraidRemoteSharesCardEditor } from "./dashboard-cards-editor";
import {
  iconTemplate,
  mdiFolder,
  mdiPower,
  mdiServerNetwork,
} from "./icons";
import { registerDashboardCard } from "./register-dashboard-card";

interface RemoteShareItem {
  name: string;
  usagePct?: number;
  used?: string;
  total?: string;
  free?: string;
  isMounted: boolean;
  mountSwitchEntityId?: string;
  usageEntityId?: string;
  mountedEntityId?: string;
}

export class UnraidRemoteSharesCard extends BaseUnraidCard {
  static override editorTag = REMOTE_SHARES_EDITOR_TAG;

  private getRemoteShares(): RemoteShareItem[] {
    const shareMap = new Map<string, RemoteShareItem>();
    if (!this.hass?.states) return [];

    const device = this.getActiveDevice();
    const deviceId = device?.id;

    for (const [entityId, stateObj] of Object.entries(this.agentStates)) {
      if (deviceId && this.hass.entities) {
        const ent = this.hass.entities[entityId];
        if (ent && ent.device_id && ent.device_id !== deviceId) continue;
      }

      // Check remote share pattern
      const match = entityId.match(/_remote_share_([a-zA-Z0-9_-]+)_(usage|mounted|mount)$/i);
      if (!match || !match[1] || !match[2]) continue;

      const shareKey = match[1].toLowerCase();
      const shareName = (stateObj.attributes?.friendly_name as string) || match[1] || "Remote Share";
      const cleanName = shareName
        .replace(/^(?:.*?\s+)?Remote Share\s+/i, "")
        .replace(/\s+(?:usage|mounted|mount)$/i, "")
        .trim();

      if (!shareMap.has(shareKey)) {
        shareMap.set(shareKey, {
          name: cleanName,
          isMounted: true,
        });
      }

      const item = shareMap.get(shareKey)!;
      const prop = match[2].toLowerCase();

      if (prop === "usage") {
        item.usageEntityId = entityId;
        const num = parseFloat(stateObj.state);
        item.usagePct = !isNaN(num) ? Math.round(num) : undefined;
        item.used = stateObj.attributes?.used as string;
        item.total = stateObj.attributes?.total as string;
        item.free = stateObj.attributes?.free as string;
      } else if (prop === "mounted") {
        item.mountedEntityId = entityId;
        item.isMounted = stateObj.state === "on" || stateObj.state === "true";
      } else if (prop === "mount") {
        item.mountSwitchEntityId = entityId;
        if (!item.mountedEntityId) {
          item.isMounted = stateObj.state === "on";
        }
      }
    }

    return Array.from(shareMap.values()).sort((a, b) => a.name.localeCompare(b.name));
  }

  private handleToggleMount(item: RemoteShareItem): void {
    if (!item.mountSwitchEntityId) return;
    if (item.isMounted) {
      if (!confirm(`Are you sure you want to unmount remote share "${item.name}"?`)) {
        return;
      }
    }
    this.toggleEntity(item.mountSwitchEntityId);
  }

  protected override render(): TemplateResult {
    const device = this.getActiveDevice();
    const serverName = this.config.title || device?.name_by_user || device?.name || "Unraid Server";
    const remoteShares = this.getRemoteShares();

    return html`
      <ha-card>
        ${this.renderHeader(
          serverName,
          "Remote SMB & NFS Shares",
          mdiServerNetwork,
          html`
            <span class="badge ${remoteShares.some((s) => s.isMounted) ? "badge-online" : ""}">
              <span class="pulse-dot"></span>
              <span>${remoteShares.length} Discovered</span>
            </span>
          `
        )}

        ${remoteShares.length === 0
          ? html`
              <div class="empty-state">
                ${iconTemplate(mdiServerNetwork, 32)}
                <div class="empty-title">No Remote Shares Found</div>
                <div class="empty-subtext">Mount remote SMB or NFS shares using the Unassigned Devices plugin on Unraid.</div>
              </div>
            `
          : html`
              <div class="disk-list">
                ${remoteShares.map((share) => {
                  return html`
                    <div class="disk-row">
                      <div
                        class="disk-main"
                        @click=${() => share.usageEntityId && this.openMoreInfo(share.usageEntityId)}
                        style="${share.usageEntityId ? "cursor: pointer;" : ""}"
                      >
                        <span class="disk-icon ${share.isMounted ? "disk-online" : "disk-standby"}">
                          ${iconTemplate(mdiFolder, 18)}
                        </span>
                        <div class="disk-info">
                          <span class="disk-name">${share.name}</span>
                          <span class="disk-subtext">
                            ${share.isMounted
                              ? share.used && share.total
                                ? `${share.used} / ${share.total}`
                                : share.usagePct !== undefined
                                ? `${share.usagePct}% used`
                                : "Mounted"
                              : "Unmounted"}
                          </span>
                        </div>
                      </div>

                      <div class="disk-meta" style="align-items: center; gap: 8px;">
                        ${share.usagePct !== undefined
                          ? html`<span class="disk-temp">${share.usagePct}%</span>`
                          : nothing}
                        ${share.mountSwitchEntityId
                          ? html`
                              <button
                                class="btn-icon ${share.isMounted ? "active" : ""}"
                                @click=${() => this.handleToggleMount(share)}
                                title="${share.isMounted ? "Unmount Remote Share" : "Mount Remote Share"}"
                                style="border: none; background: transparent; cursor: pointer; color: ${share.isMounted ? "var(--unraid-online)" : "var(--unraid-subtext)"}; padding: 4px;"
                              >
                                ${iconTemplate(mdiPower, 18)}
                              </button>
                            `
                          : html`
                              <span class="badge ${share.isMounted ? "badge-online" : ""}">
                                ${share.isMounted ? "MOUNTED" : "UNMOUNTED"}
                              </span>
                            `}
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
  tag: REMOTE_SHARES_CARD_TAG,
  editorTag: REMOTE_SHARES_EDITOR_TAG,
  card: UnraidRemoteSharesCard,
  editor: UnraidRemoteSharesCardEditor,
  name: "Unraid Remote Shares Card",
  description: "Monitor and mount remote network SMB/NFS storage shares",
});
