import { html, nothing, type TemplateResult } from "lit";
import {
  UPS_CARD_TAG,
  UPS_EDITOR_TAG,
} from "./config";
import { BaseUnraidCard } from "./dashboard-cards-base";
import { UnraidUpsCardEditor } from "./dashboard-cards-editor";
import {
  mdiFlash,
} from "./icons";
import { registerDashboardCard } from "./register-dashboard-card";

export function formatRuntime(
  state?: string | null,
  attributes?: Record<string, unknown>
): string | null {
  if (!state || state === "unavailable" || state === "unknown") {
    return null;
  }
  const trimmed = state.trim();
  if (!trimmed) {
    return null;
  }

  // If already formatted text (e.g., "1 hour 41 minutes")
  // Strip redundant trailing " min" if the string already contains duration units
  if (/[a-zA-Z]/.test(trimmed)) {
    return trimmed.replace(/(\b(?:minute|minutes|hour|hours|sec|second|seconds|min|mins)\b.*)\s+min$/i, "$1");
  }

  // If numeric (raw minutes or seconds)
  const num = Number(trimmed);
  if (Number.isFinite(num)) {
    const unit = typeof attributes?.unit_of_measurement === "string" ? attributes.unit_of_measurement.toLowerCase() : "";
    let totalMinutes = num;
    if (unit === "s" || unit === "sec" || unit === "seconds") {
      totalMinutes = Math.round(num / 60);
    } else {
      totalMinutes = Math.round(num);
    }

    const hours = Math.floor(totalMinutes / 60);
    const mins = totalMinutes % 60;

    if (hours > 0) {
      return mins > 0
        ? `${hours} hour${hours > 1 ? "s" : ""} ${mins} minute${mins > 1 ? "s" : ""}`
        : `${hours} hour${hours > 1 ? "s" : ""}`;
    }
    return `${mins} minute${mins !== 1 ? "s" : ""}`;
  }

  return trimmed;
}

export class UnraidUpsCard extends BaseUnraidCard {
  static override editorTag = UPS_EDITOR_TAG;

  protected override render(): TemplateResult {
    const statusState = this.getEntity("ups_status");
    const connectedState = this.getEntity("ups_connected", "binary_sensor");
    const batteryState = this.getEntity("ups_battery");
    const loadState = this.getEntity("ups_load");
    const runtimeState = this.getEntity("ups_runtime");
    const powerState = this.getEntity("ups_power");
    const voltageOut = this.getEntity("ups_output_voltage");
    const healthState = this.getEntity("ups_battery_health");
    const energyState = this.getEntity("ups_energy");

    const isConnected = connectedState?.state === "on";
    const hasStatus = Boolean(
      (statusState && statusState.state !== "unavailable" && statusState.state !== "unknown") ||
      isConnected
    );
    const status =
      statusState && statusState.state !== "unavailable" && statusState.state !== "unknown"
        ? statusState.state
        : isConnected
        ? "Online"
        : (statusState?.state || "Unavailable");
    const isOnline = hasStatus && (status.toLowerCase().includes("online") || isConnected);
    const isBattery = hasStatus && (status.toLowerCase().includes("battery") || status.toLowerCase().includes("discharge"));
    const isUnavailable = !hasStatus || status === "Unavailable" || status === "unavailable";

    const hasBattery = Boolean(batteryState && batteryState.state !== "unavailable" && batteryState.state !== "unknown");
    const batteryPct = hasBattery && batteryState ? Math.round(Number(batteryState.state) || 0) : null;

    const hasLoad = Boolean(loadState && loadState.state !== "unavailable" && loadState.state !== "unknown");
    const loadPct = hasLoad && loadState ? Math.round(Number(loadState.state) || 0) : null;

    const hasPower = Boolean(powerState && powerState.state !== "unavailable" && powerState.state !== "unknown");
    const powerW = hasPower && powerState ? `${powerState.state} W` : null;

    const runtimeFormatted = formatRuntime(runtimeState?.state, runtimeState?.attributes);

    const hasVoltage = Boolean(voltageOut && voltageOut.state !== "unavailable" && voltageOut.state !== "unknown");
    const voltageV = hasVoltage && voltageOut ? `${voltageOut.state} V` : null;

    const hasEnergy = Boolean(energyState && energyState.state !== "unavailable" && energyState.state !== "unknown");
    const energyFormatted =
      hasEnergy && energyState
        ? `${energyState.state} ${energyState.attributes?.unit_of_measurement || "kWh"}`
        : null;

    const hasHealth = Boolean(healthState && healthState.state !== "unavailable" && healthState.state !== "unknown");
    const fallbackHealth =
      (batteryState?.attributes?.ups_status as string) ||
      (statusState?.attributes?.ups_status as string) ||
      (isOnline ? "Normal" : isConnected ? "Online" : null);
    const health = hasHealth && healthState ? healthState.state : fallbackHealth;

    const badge = html`
      <span class="badge ${isUnavailable ? "badge-standby" : isOnline ? "badge-online" : isBattery ? "badge-warning" : "badge-error"}">
        ${!isUnavailable ? html`<span class="pulse-dot"></span>` : nothing}
        <span>${isUnavailable ? "Unavailable" : status}</span>
      </span>
    `;

    return html`
      <ha-card>
        ${this.renderHeader(
          this.config.title || "UPS Power & Battery",
          (statusState?.attributes?.model as string) || "Uninterruptible Power Supply",
          mdiFlash,
          badge
        )}
        <div class="rings-grid" style="grid-template-columns: repeat(2, 1fr);">
          <button
            type="button"
            ?disabled=${!(batteryState)}
            class="interactive ring-card"
            @click=${() => batteryState && this.openMoreInfo(batteryState.entity_id)}
            title="Click to view Battery details"
          >
            <span data-block
              class="ring-gauge"
              style="--pct: ${batteryPct ?? 0}; --ring-color: ${batteryPct === null ? "var(--unraid-border)" : batteryPct < 20 ? "var(--unraid-error)" : batteryPct < 50 ? "var(--unraid-warning)" : "var(--unraid-online)"}"
            >
              <span class="ring-content">${batteryPct !== null ? `${batteryPct}%` : "—"}</span>
            </span>
            <span class="ring-label">Battery Level</span>
            <span class="ring-subtext">${runtimeFormatted ? `${runtimeFormatted} left` : batteryPct !== null ? "Healthy" : "No Data"}</span>
          </button>
          <button
            type="button"
            ?disabled=${!(loadState)}
            class="interactive ring-card"
            @click=${() => loadState && this.openMoreInfo(loadState.entity_id)}
            title="Click to view Load details"
          >
            <span data-block
              class="ring-gauge"
              style="--pct: ${loadPct ?? 0}; --ring-color: ${loadPct === null ? "var(--unraid-border)" : loadPct > 80 ? "var(--unraid-error)" : loadPct > 50 ? "var(--unraid-warning)" : "var(--unraid-info)"}"
            >
              <span class="ring-content">${loadPct !== null ? `${loadPct}%` : "—"}</span>
            </span>
            <span class="ring-label">UPS Load</span>
            <span class="ring-subtext">${powerW || (loadPct !== null ? `${loadPct}% capacity` : "No Data")}</span>
          </button>
        </div>

        <div class="divider"></div>
        <div class="detail-grid">
          <button
            type="button"
            ?disabled=${!(runtimeState)}
            class="interactive detail-item"
            @click=${() => runtimeState && this.openMoreInfo(runtimeState.entity_id)}
            title="Click to view Runtime details"
          >
            <span class="detail-label">Runtime Remaining</span>
            <span class="detail-val">${runtimeFormatted || "—"}</span>
          </button>
          <button
            type="button"
            ?disabled=${!(powerState)}
            class="interactive detail-item"
            @click=${() => powerState && this.openMoreInfo(powerState.entity_id)}
            title="Click to view Power details"
          >
            <span class="detail-label">Power Consumption</span>
            <span class="detail-val">${powerW || "—"}</span>
          </button>
          <button
            type="button"
            ?disabled=${!(voltageOut || energyState)}
            class="interactive detail-item"
            @click=${() => {
              const target = voltageOut || energyState;
              if (target) this.openMoreInfo(target.entity_id);
            }}
            title="${voltageOut ? "Click to view Voltage details" : "Click to view Energy details"}"
          >
            <span class="detail-label">${hasVoltage ? "Output Voltage" : hasEnergy ? "Energy Consumed" : "Output Voltage"}</span>
            <span class="detail-val">${voltageV || energyFormatted || "—"}</span>
          </button>
          <button
            type="button"
            ?disabled=${!(healthState || batteryState)}
            class="interactive detail-item"
            @click=${() => {
              const target = healthState || batteryState;
              if (target) this.openMoreInfo(target.entity_id);
            }}
            title="Click to view Battery Health details"
          >
            <span class="detail-label">Battery Health</span>
            <span class="detail-val" style="${health && !health.toLowerCase().includes("fail") ? "color: var(--unraid-online);" : ""}">${health || "—"}</span>
          </button>
        </div>
      </ha-card>
    `;
  }
}

registerDashboardCard({
  tag: UPS_CARD_TAG,
  editorTag: UPS_EDITOR_TAG,
  card: UnraidUpsCard,
  editor: UnraidUpsCardEditor,
  name: "Unraid Power & UPS Card",
  description: "Monitor UPS battery level, power draw in Watts, load %, and estimated runtime.",
});
