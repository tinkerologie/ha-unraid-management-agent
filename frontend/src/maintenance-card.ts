import { html, nothing, type TemplateResult } from "lit";
import {
  MAINTENANCE_CARD_TAG,
  MAINTENANCE_EDITOR_TAG,
} from "./config";
import { BaseUnraidCard, formatDataSize, formatFriendlyDateTime } from "./dashboard-cards-base";
import { UnraidMaintenanceCardEditor } from "./dashboard-cards-editor";
import {
  iconTemplate,
  mdiClockOutline,
  mdiDownload,
  mdiShieldCheck,
  mdiWrench,
} from "./icons";
import { registerDashboardCard } from "./register-dashboard-card";

export class UnraidMaintenanceCard extends BaseUnraidCard {
  static override editorTag = MAINTENANCE_EDITOR_TAG;

  protected override render(): TemplateResult {
    const device = this.getActiveDevice();
    const serverName = this.config.title || device?.name_by_user || device?.name || "Unraid Server";

    const lastParity = this.getEntity("last_parity_check");
    const nextParity = this.getEntity("next_parity_check");
    const parityRunning = this.getEntity("parity_check_running", "binary_sensor");
    const parityValid = this.getEntity("parity_valid", "binary_sensor");
    const flashUsage = this.getEntity("flash_usage");
    const flashFree = this.getEntity("flash_free_space");
    const pluginUpdates = this.getEntity("plugins_with_updates") || this.getEntity("plugin_updates");
    const containerUpdates = this.getEntity("container_updates_available");

    const isCheckRunning = parityRunning?.state === "on";
    const isParityInvalid = parityValid?.state === "on"; // parity_valid is Problem sensor: on means problem/invalid

    const flashFreeText = formatDataSize(flashFree);
    const flashPct = Math.round(Number(flashUsage?.state) || 0);
    const numPluginUpdates = Number(pluginUpdates?.state) || 0;
    const numContainerUpdates = Number(containerUpdates?.state) || 0;
    const totalUpdates = numPluginUpdates + numContainerUpdates;

    const lastDuration = lastParity?.attributes?.duration || lastParity?.attributes?.last_duration;
    const lastResult = lastParity?.attributes?.result || lastParity?.state;
    const lastErrors = lastParity?.attributes?.errors;

    return html`
      <ha-card>
        <div class="card-content">
        ${this.renderHeader(
          serverName,
          "Maintenance & Operations",
          mdiWrench,
          html`
            <span class="badge ${totalUpdates > 0 ? "badge-warning" : "badge-online"}">
              <span class="pulse-dot"></span>
              <span>${totalUpdates > 0 ? `${totalUpdates} Updates` : "Up to Date"}</span>
            </span>
          `
        )}

        <div class="rings-grid">
          <button
            type="button"
            ?disabled=${!(flashUsage)}
            class="interactive ring-card"
            @click=${() => flashUsage && this.openMoreInfo(flashUsage.entity_id)}
            title="Click for Flash USB details"
          >
            <span data-block
              class="ring-gauge"
              style="--pct: ${flashPct}; --ring-color: ${flashPct > 80 ? "var(--unraid-error)" : flashPct > 60 ? "var(--unraid-warning)" : "var(--unraid-online)"}"
            >
              <span class="ring-content">${flashPct}%</span>
            </span>
            <span class="ring-label">Flash Boot Drive</span>
            <span class="ring-subtext">${flashFreeText ? `${flashFreeText} Free` : "USB Boot Drive"}</span>
          </button>

          <button
            type="button"
            ?disabled=${!(lastParity)}
            class="interactive ring-card"
            @click=${() => lastParity && this.openMoreInfo(lastParity.entity_id)}
            title="Click for Parity status"
          >
            <span data-block
              class="ring-gauge"
              style="--pct: ${isCheckRunning ? 50 : 100}; --ring-color: ${isParityInvalid ? "var(--unraid-error)" : "var(--unraid-online)"}"
            >
              <span class="ring-content">${isCheckRunning ? "SYNC" : isParityInvalid ? "FAIL" : "OK"}</span>
            </span>
            <span class="ring-label">Parity Health</span>
            <span class="ring-subtext">${lastErrors !== undefined ? `${lastErrors} Sync Errors` : "Parity Protected"}</span>
          </button>
        </div>

        <div class="divider"></div>

        <div class="disk-list">
          <button
            type="button"
            ?disabled=${!(lastParity)}
            class="interactive disk-row"
            @click=${() => lastParity && this.openMoreInfo(lastParity.entity_id)}
          >
            <span data-block class="disk-main">
              <span class="disk-icon ${lastErrors ? "disk-warning" : "disk-online"}">
                ${iconTemplate(mdiShieldCheck, 18)}
              </span>
              <span data-block class="disk-info">
                <span class="disk-name">Last Parity Check</span>
                <span class="disk-subtext">
                  ${lastResult && lastResult !== lastParity?.state ? lastResult : "Completed"}
                  ${lastDuration ? ` • Duration: ${lastDuration}` : ""}
                  ${lastErrors !== undefined ? (lastErrors === 0 ? " • 0 sync errors" : ` • ${lastErrors} errors`) : ""}
                </span>
              </span>
            </span>
            <span data-block class="disk-meta">
              <span class="disk-temp">${formatFriendlyDateTime(lastParity?.state)}</span>
            </span>
          </button>

          ${nextParity?.state && nextParity.state !== "unavailable" && nextParity.state !== "unknown"
            ? html`
                <button
                  type="button"
                  class="interactive disk-row"
                  @click=${() => this.openMoreInfo(nextParity.entity_id)}
                >
                  <span data-block class="disk-main">
                    <span class="disk-icon disk-online">
                      ${iconTemplate(mdiClockOutline, 18)}
                    </span>
                    <span data-block class="disk-info">
                      <span class="disk-name">Next Scheduled Parity</span>
                      <span class="disk-subtext">
                        Automated Parity Verification${nextParity.attributes?.mode ? ` (${typeof nextParity.attributes.mode === "string" ? nextParity.attributes.mode.charAt(0).toUpperCase() + nextParity.attributes.mode.slice(1) : nextParity.attributes.mode})` : ""}
                      </span>
                    </span>
                  </span>
                  <span data-block class="disk-meta">
                    <span class="disk-temp">${formatFriendlyDateTime(nextParity.state)}</span>
                  </span>
                </button>
              `
            : nothing}

          ${pluginUpdates
            ? html`
                <button
                  type="button"
                  class="interactive disk-row"
                  @click=${() => this.openMoreInfo(pluginUpdates.entity_id)}
                >
                  <span data-block class="disk-main">
                    <span class="disk-icon ${numPluginUpdates > 0 ? "disk-warning" : "disk-online"}">
                      ${iconTemplate(mdiDownload, 18)}
                    </span>
                    <span data-block class="disk-info">
                      <span class="disk-name">Plugin Updates</span>
                      <span class="disk-subtext">${numPluginUpdates > 0 ? `${numPluginUpdates} plugin updates pending` : "All plugins are up to date"}</span>
                    </span>
                  </span>
                  <span data-block class="disk-meta">
                    <span class="badge ${numPluginUpdates > 0 ? "badge-warning" : "badge-online"}">
                      ${numPluginUpdates > 0 ? `${numPluginUpdates} NEW` : "CURRENT"}
                    </span>
                  </span>
                </button>
              `
            : nothing}

          ${containerUpdates
            ? html`
                <button
                  type="button"
                  class="interactive disk-row"
                  @click=${() => this.openMoreInfo(containerUpdates.entity_id)}
                >
                  <span data-block class="disk-main">
                    <span class="disk-icon ${numContainerUpdates > 0 ? "disk-warning" : "disk-online"}">
                      ${iconTemplate(mdiDownload, 18)}
                    </span>
                    <span data-block class="disk-info">
                      <span class="disk-name">Docker Image Updates</span>
                      <span class="disk-subtext">${numContainerUpdates > 0 ? `${numContainerUpdates} container image updates available` : "All container images are current"}</span>
                    </span>
                  </span>
                  <span data-block class="disk-meta">
                    <span class="badge ${numContainerUpdates > 0 ? "badge-warning" : "badge-online"}">
                      ${numContainerUpdates > 0 ? `${numContainerUpdates} NEW` : "CURRENT"}
                    </span>
                  </span>
                </button>
              `
            : nothing}
        </div>
      </div>
      </ha-card>
    `;
  }
}

registerDashboardCard({
  tag: MAINTENANCE_CARD_TAG,
  editorTag: MAINTENANCE_EDITOR_TAG,
  card: UnraidMaintenanceCard,
  editor: UnraidMaintenanceCardEditor,
  name: "Unraid Maintenance Card",
  description: "Parity verification history, flash drive health, and plugin/container update status",
});
