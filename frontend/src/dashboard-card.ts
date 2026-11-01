import { html, nothing, type TemplateResult } from "lit";
import {
  DASHBOARD_CARD_TAG,
  DASHBOARD_EDITOR_TAG,
} from "./config";
import { BaseUnraidCard } from "./dashboard-cards-base";
import { UnraidDashboardCardEditor } from "./dashboard-cards-editor";
import {
  iconTemplate,
  mdiBell,
  mdiDatabase,
  mdiDocker,
  mdiExpansionCard,
  mdiFan,
  mdiFlash,
  mdiFolder,
  mdiHarddisk,
  mdiHarddiskPlus,
  mdiLanConnect,
  mdiMonitor,
  mdiServer,
  mdiServerNetwork,
  mdiWrench,
} from "./icons";
import { registerDashboardCard } from "./register-dashboard-card";

import "./server-card";
import "./storage-card";
import "./shares-card";
import "./network-card";
import "./docker-card";
import "./ups-card";
import "./vm-card";
import "./zfs-card";
import "./fans-card";
import "./gpu-card";
import "./notifications-card";
import "./maintenance-card";
import "./remote-shares-card";
import "./unassigned-devices-card";

type ActiveTab =
  | "overview"
  | "storage"
  | "zfs"
  | "shares"
  | "remote-shares"
  | "unassigned"
  | "network"
  | "docker"
  | "vms"
  | "fans"
  | "gpu"
  | "ups"
  | "maintenance"
  | "notifications";

const TABS: [ActiveTab, string, string][] = [
  ["overview", mdiServer, "Overview"],
  ["storage", mdiHarddisk, "Storage"],
  ["zfs", mdiDatabase, "ZFS"],
  ["shares", mdiFolder, "Shares"],
  ["remote-shares", mdiServerNetwork, "Remote"],
  ["unassigned", mdiHarddiskPlus, "Unassigned"],
  ["network", mdiLanConnect, "Network"],
  ["docker", mdiDocker, "Docker"],
  ["vms", mdiMonitor, "VMs"],
  ["fans", mdiFan, "Fans"],
  ["gpu", mdiExpansionCard, "GPU"],
  ["ups", mdiFlash, "UPS"],
  ["maintenance", mdiWrench, "Maintenance"],
  ["notifications", mdiBell, "Notifications"],
];

export class UnraidDashboardCard extends BaseUnraidCard {
  static override editorTag = DASHBOARD_EDITOR_TAG;

  static override properties = {
    ...BaseUnraidCard.properties,
    _activeTab: { state: true },
  };

  declare _activeTab: ActiveTab;

  constructor() {
    super();
    this._activeTab = "overview";
  }

  private readonly _onTabKeydown = async (event: KeyboardEvent): Promise<void> => {
    const current = TABS.findIndex(([id]) => id === this._activeTab);
    const rtl = getComputedStyle(this).direction === "rtl";
    const next = {
      ArrowRight: current + (rtl ? -1 : 1),
      ArrowLeft: current + (rtl ? 1 : -1),
      Home: 0,
      End: TABS.length - 1,
    }[event.key];
    if (next === undefined) return;
    event.preventDefault();
    this._activeTab = TABS[(next + TABS.length) % TABS.length]![0];
    await this.updateComplete;
    this.shadowRoot?.querySelector<HTMLElement>(`#tab-${this._activeTab}`)?.focus();
  };

  protected override render(): TemplateResult {
    const device = this.getActiveDevice();
    const serverName = this.config.title || device?.name_by_user || device?.name || "Unraid Server";

    return html`
      <ha-card style="gap: var(--ha-space-3, 12px);">
        <div class="header">
          <div class="header-main">
            <div class="header-icon">${iconTemplate(mdiServer, 22)}</div>
            <div class="header-titles">
              <span class="header-title">${serverName} Dashboard</span>
              <span class="header-subtitle">Unraid Management Agent</span>
            </div>
          </div>
        </div>
        <div class="tab-strip" role="tablist" aria-label="Dashboard section" @keydown=${this._onTabKeydown}>
          ${TABS.map(
            ([id, icon, label]) => html`
              <button
                type="button"
                role="tab"
                id="tab-${id}"
                class="tab-btn ${this._activeTab === id ? "active" : ""}"
                aria-selected=${this._activeTab === id}
                aria-controls="dashboard-panel"
                tabindex=${this._activeTab === id ? 0 : -1}
                @click=${() => (this._activeTab = id)}
              >
                ${iconTemplate(icon, 14)} ${label}
              </button>
            `
          )}
        </div>
        <div role="tabpanel" id="dashboard-panel" aria-labelledby="tab-${this._activeTab}">
          ${this._activeTab === "overview"
            ? html`<unraid-management-agent-server-card .hass=${this.hass} .config=${{ ...this.config, type: "custom:unraid-management-agent-server-card", embedded: true }}></unraid-management-agent-server-card>`
            : nothing}
          ${this._activeTab === "storage"
            ? html`<unraid-management-agent-storage-card .hass=${this.hass} .config=${{ ...this.config, type: "custom:unraid-management-agent-storage-card", embedded: true }}></unraid-management-agent-storage-card>`
            : nothing}
          ${this._activeTab === "zfs"
            ? html`<unraid-management-agent-zfs-card .hass=${this.hass} .config=${{ ...this.config, type: "custom:unraid-management-agent-zfs-card", embedded: true }}></unraid-management-agent-zfs-card>`
            : nothing}
          ${this._activeTab === "shares"
            ? html`<unraid-management-agent-shares-card .hass=${this.hass} .config=${{ ...this.config, type: "custom:unraid-management-agent-shares-card", embedded: true }}></unraid-management-agent-shares-card>`
            : nothing}
          ${this._activeTab === "remote-shares"
            ? html`<unraid-management-agent-remote-shares-card .hass=${this.hass} .config=${{ ...this.config, type: "custom:unraid-management-agent-remote-shares-card", embedded: true }}></unraid-management-agent-remote-shares-card>`
            : nothing}
          ${this._activeTab === "unassigned"
            ? html`<unraid-management-agent-unassigned-devices-card .hass=${this.hass} .config=${{ ...this.config, type: "custom:unraid-management-agent-unassigned-devices-card", embedded: true }}></unraid-management-agent-unassigned-devices-card>`
            : nothing}
          ${this._activeTab === "network"
            ? html`<unraid-management-agent-network-card .hass=${this.hass} .config=${{ ...this.config, type: "custom:unraid-management-agent-network-card", embedded: true }}></unraid-management-agent-network-card>`
            : nothing}
          ${this._activeTab === "docker"
            ? html`<unraid-management-agent-docker-card .hass=${this.hass} .config=${{ ...this.config, type: "custom:unraid-management-agent-docker-card", embedded: true }}></unraid-management-agent-docker-card>`
            : nothing}
          ${this._activeTab === "vms"
            ? html`<unraid-management-agent-vm-card .hass=${this.hass} .config=${{ ...this.config, type: "custom:unraid-management-agent-vm-card", embedded: true }}></unraid-management-agent-vm-card>`
            : nothing}
          ${this._activeTab === "fans"
            ? html`<unraid-management-agent-fans-card .hass=${this.hass} .config=${{ ...this.config, type: "custom:unraid-management-agent-fans-card", embedded: true }}></unraid-management-agent-fans-card>`
            : nothing}
          ${this._activeTab === "gpu"
            ? html`<unraid-management-agent-gpu-card .hass=${this.hass} .config=${{ ...this.config, type: "custom:unraid-management-agent-gpu-card", embedded: true }}></unraid-management-agent-gpu-card>`
            : nothing}
          ${this._activeTab === "ups"
            ? html`<unraid-management-agent-ups-card .hass=${this.hass} .config=${{ ...this.config, type: "custom:unraid-management-agent-ups-card", embedded: true }}></unraid-management-agent-ups-card>`
            : nothing}
          ${this._activeTab === "maintenance"
            ? html`<unraid-management-agent-maintenance-card .hass=${this.hass} .config=${{ ...this.config, type: "custom:unraid-management-agent-maintenance-card", embedded: true }}></unraid-management-agent-maintenance-card>`
            : nothing}
          ${this._activeTab === "notifications"
            ? html`<unraid-management-agent-notifications-card .hass=${this.hass} .config=${{ ...this.config, type: "custom:unraid-management-agent-notifications-card", embedded: true }}></unraid-management-agent-notifications-card>`
            : nothing}
        </div>
      </ha-card>
    `;
  }
}

registerDashboardCard({
  tag: DASHBOARD_CARD_TAG,
  editorTag: DASHBOARD_EDITOR_TAG,
  card: UnraidDashboardCard,
  editor: UnraidDashboardCardEditor,
  name: "Unraid Unified Dashboard Card",
  description: "All-in-one Unraid master card with tabbed overview, storage, ZFS, docker, UPS, and VM monitoring.",
});
