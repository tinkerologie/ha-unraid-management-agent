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

  protected override render(): TemplateResult {
    const device = this.getActiveDevice();
    const serverName = this.config.title || device?.name_by_user || device?.name || "Unraid Server";

    return html`
      <ha-card style="gap: 12px;">
        <div class="header">
          <div class="header-main">
            <div class="header-icon">${iconTemplate(mdiServer, 22)}</div>
            <div class="header-titles">
              <span class="header-title">${serverName} Dashboard</span>
              <span class="header-subtitle">Unraid Management Agent</span>
            </div>
          </div>
        </div>
        <div class="tab-strip" role="group" aria-label="Dashboard section" style="display: flex; flex-wrap: wrap; gap: 6px;">
          <button
            class="tab-btn ${this._activeTab === "overview" ? "active" : ""}"
            aria-pressed=${this._activeTab === "overview"}
            @click=${() => (this._activeTab = "overview")}
          >
            ${iconTemplate(mdiServer, 14)} Overview
          </button>
          <button
            class="tab-btn ${this._activeTab === "storage" ? "active" : ""}"
            aria-pressed=${this._activeTab === "storage"}
            @click=${() => (this._activeTab = "storage")}
          >
            ${iconTemplate(mdiHarddisk, 14)} Storage
          </button>
          <button
            class="tab-btn ${this._activeTab === "zfs" ? "active" : ""}"
            aria-pressed=${this._activeTab === "zfs"}
            @click=${() => (this._activeTab = "zfs")}
          >
            ${iconTemplate(mdiDatabase, 14)} ZFS
          </button>
          <button
            class="tab-btn ${this._activeTab === "shares" ? "active" : ""}"
            aria-pressed=${this._activeTab === "shares"}
            @click=${() => (this._activeTab = "shares")}
          >
            ${iconTemplate(mdiFolder, 14)} Shares
          </button>
          <button
            class="tab-btn ${this._activeTab === "remote-shares" ? "active" : ""}"
            aria-pressed=${this._activeTab === "remote-shares"}
            @click=${() => (this._activeTab = "remote-shares")}
          >
            ${iconTemplate(mdiServerNetwork, 14)} Remote
          </button>
          <button
            class="tab-btn ${this._activeTab === "unassigned" ? "active" : ""}"
            aria-pressed=${this._activeTab === "unassigned"}
            @click=${() => (this._activeTab = "unassigned")}
          >
            ${iconTemplate(mdiHarddiskPlus, 14)} Unassigned
          </button>
          <button
            class="tab-btn ${this._activeTab === "network" ? "active" : ""}"
            aria-pressed=${this._activeTab === "network"}
            @click=${() => (this._activeTab = "network")}
          >
            ${iconTemplate(mdiLanConnect, 14)} Network
          </button>
          <button
            class="tab-btn ${this._activeTab === "docker" ? "active" : ""}"
            aria-pressed=${this._activeTab === "docker"}
            @click=${() => (this._activeTab = "docker")}
          >
            ${iconTemplate(mdiDocker, 14)} Docker
          </button>
          <button
            class="tab-btn ${this._activeTab === "vms" ? "active" : ""}"
            aria-pressed=${this._activeTab === "vms"}
            @click=${() => (this._activeTab = "vms")}
          >
            ${iconTemplate(mdiMonitor, 14)} VMs
          </button>
          <button
            class="tab-btn ${this._activeTab === "fans" ? "active" : ""}"
            aria-pressed=${this._activeTab === "fans"}
            @click=${() => (this._activeTab = "fans")}
          >
            ${iconTemplate(mdiFan, 14)} Fans
          </button>
          <button
            class="tab-btn ${this._activeTab === "gpu" ? "active" : ""}"
            aria-pressed=${this._activeTab === "gpu"}
            @click=${() => (this._activeTab = "gpu")}
          >
            ${iconTemplate(mdiExpansionCard, 14)} GPU
          </button>
          <button
            class="tab-btn ${this._activeTab === "ups" ? "active" : ""}"
            aria-pressed=${this._activeTab === "ups"}
            @click=${() => (this._activeTab = "ups")}
          >
            ${iconTemplate(mdiFlash, 14)} UPS
          </button>
          <button
            class="tab-btn ${this._activeTab === "maintenance" ? "active" : ""}"
            aria-pressed=${this._activeTab === "maintenance"}
            @click=${() => (this._activeTab = "maintenance")}
          >
            ${iconTemplate(mdiWrench, 14)} Maintenance
          </button>
          <button
            class="tab-btn ${this._activeTab === "notifications" ? "active" : ""}"
            aria-pressed=${this._activeTab === "notifications"}
            @click=${() => (this._activeTab = "notifications")}
          >
            ${iconTemplate(mdiBell, 14)} Notifications
          </button>
        </div>
        <div>
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
