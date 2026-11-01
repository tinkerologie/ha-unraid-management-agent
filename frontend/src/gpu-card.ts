import { html, nothing, type TemplateResult } from "lit";
import {
  GPU_CARD_TAG,
  GPU_EDITOR_TAG,
} from "./config";
import { BaseUnraidCard } from "./dashboard-cards-base";
import { UnraidGpuCardEditor } from "./dashboard-cards-editor";
import {
  iconTemplate,
  mdiExpansionCard,
} from "./icons";
import { registerDashboardCard } from "./register-dashboard-card";

interface GPUItem {
  index: number;
  name: string;
  /** The name is the GPU device's (as named by the user, if renamed) */
  nameFromDevice?: boolean;
  driver?: string;
  utilizationPct?: number;
  utilizationEntityId?: string;
  temp?: number;
  tempEntityId?: string;
  power?: number;
  powerEntityId?: string;
  energy?: number;
  energyEntityId?: string;
  memUtilPct?: number;
  memUtilEntityId?: string;
}

// Metrics the card shows, by translation key of the sensors on a GPU device
// (the "Show GPUs as separate devices" option)
const GPU_DEVICE_METRICS: Record<string, string> = {
  gpu_device_utilization: "utilization",
  gpu_device_temperature: "temperature",
  gpu_device_power: "power",
  gpu_device_energy: "energy",
  gpu_device_vram_usage: "vram_usage",
};

export class UnraidGpuCard extends BaseUnraidCard {
  static override editorTag = GPU_EDITOR_TAG;

  private getGpus(): GPUItem[] {
    const gpuMap = new Map<string, GPUItem>();
    if (!this.hass?.states) return [];

    const device = this.getActiveDevice();
    const deviceId = device?.id;
    const cleanName = device?.name
      ? this.slugifyDeviceName(device.name)
      : undefined;

    for (const [entityId, stateObj] of Object.entries(this.agentStates)) {
      if (!entityId.startsWith("sensor.")) continue;

      const ent = this.hass.entities?.[entityId];
      // Each GPU's sensors sit on a "GPU · <name>" child device of the server
      const entDevice = ent?.device_id ? this.hass.devices?.[ent.device_id] : undefined;
      const gpuDevice = entDevice?.parent_device_id ? entDevice : undefined;
      if (deviceId && ent?.device_id) {
        if (ent.device_id !== deviceId && gpuDevice?.parent_device_id !== deviceId) {
          continue;
        }
      } else if (cleanName && !entityId.includes(cleanName)) {
        continue;
      }

      // A GPU device's sensors are told apart by translation key: their entity
      // IDs can carry another GPU's name, or a "_2" suffix, after GPUs swap
      // indexes. Other sensors are recognized by entity ID; one with a "_2"
      // suffix belongs to another GPU than the one without it.
      const match = gpuDevice
        ? undefined
        : entityId.match(
            /_gpu_(?:(.+?)_)?(utilization|temperature|power|energy|memory_utilization|vram_usage)(?:_(\d+))?$/i
          );
      const metric = gpuDevice
        ? GPU_DEVICE_METRICS[ent?.translation_key ?? ""]
        : match?.[2]?.toLowerCase();
      if (!metric) continue;

      const rawKey = gpuDevice ? gpuDevice.id : match?.[1] || "0";
      const gpuKey = gpuDevice
        ? `device:${gpuDevice.id}`
        : `${rawKey.toLowerCase()}${match?.[3] ? `#${match[3]}` : ""}`;

      if (!gpuMap.has(gpuKey)) {
        const parsedIndex = parseInt(rawKey, 10);
        const index = !isNaN(parsedIndex) ? parsedIndex : gpuMap.size;
        const friendlyName =
          typeof stateObj.attributes?.friendly_name === "string"
            ? (stateObj.attributes.friendly_name as string)
                .replace(/^(?:.*?\s+)?(?:GPU\s+)?/i, "")
                .replace(
                  /\s+(?:Utilization|Temperature|Power|Energy|VRAM|Usage).*$/i,
                  "",
                )
            : undefined;

        const deviceName =
          gpuDevice?.name_by_user ||
          gpuDevice?.name?.replace(/^GPU\s*·\s*/i, "") ||
          undefined;
        const gpuName =
          deviceName ||
          (typeof stateObj.attributes?.gpu_name === "string"
            ? (stateObj.attributes.gpu_name as string)
            : undefined) ||
          friendlyName ||
          (rawKey !== "0"
            ? rawKey.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase())
            : `GPU ${index}`);
        const driver =
          (stateObj.attributes?.gpu_driver_version as string) ||
          (stateObj.attributes?.driver_version as string) ||
          undefined;

        gpuMap.set(gpuKey, {
          index,
          name: gpuName,
          nameFromDevice: deviceName !== undefined,
          driver,
        });
      }

      const item = gpuMap.get(gpuKey)!;

      // Update name and driver from any metric attribute that provides them
      if (
        stateObj.attributes?.gpu_name &&
        !item.nameFromDevice &&
        (!item.name || item.name.startsWith("GPU "))
      ) {
        item.name = stateObj.attributes.gpu_name as string;
      }
      if (
        (stateObj.attributes?.gpu_driver_version || stateObj.attributes?.driver_version) &&
        !item.driver
      ) {
        item.driver = (stateObj.attributes.gpu_driver_version || stateObj.attributes.driver_version) as string;
      }

      const numVal = parseFloat(stateObj.state);

      if (metric === "utilization") {
        item.utilizationPct = !isNaN(numVal) ? Math.round(numVal) : undefined;
        item.utilizationEntityId = entityId;
      } else if (metric === "temperature") {
        item.temp = !isNaN(numVal) ? Math.round(numVal) : undefined;
        item.tempEntityId = entityId;
      } else if (metric === "power") {
        item.power = !isNaN(numVal) ? Math.round(numVal) : undefined;
        item.powerEntityId = entityId;
      } else if (metric === "energy") {
        item.energy = !isNaN(numVal) ? Number(numVal.toFixed(2)) : undefined;
        item.energyEntityId = entityId;
      } else if (metric === "memory_utilization" || metric === "vram_usage") {
        item.memUtilPct = !isNaN(numVal) ? Math.round(numVal) : undefined;
        item.memUtilEntityId = entityId;
      }
    }

    return Array.from(gpuMap.values()).sort((a, b) => a.index - b.index);
  }

  protected override render(): TemplateResult {
    const device = this.getActiveDevice();
    const serverName = this.config.title || device?.name_by_user || device?.name || "Unraid Server";
    const gpus = this.getGpus();

    return html`
      <ha-card>
        ${this.renderHeader(
          serverName,
          "GPU Accelerators",
          mdiExpansionCard,
          html`
            <span class="badge ${gpus.length > 0 ? "badge-online" : ""}">
              <span class="pulse-dot"></span>
              <span>${gpus.length} GPU${gpus.length === 1 ? "" : "s"}</span>
            </span>
          `
        )}

        ${gpus.length === 0
          ? html`
              <div class="empty-state">
                ${iconTemplate(mdiExpansionCard, 32)}
                <div class="empty-title">No GPU Telemetry Available</div>
                <div class="empty-subtext">Enable GPU monitoring or install NVIDIA / Intel GPU plugins to view GPU stats.</div>
              </div>
            `
          : html`
              <div class="gpu-grid" style="display: flex; flex-direction: column; gap: var(--ha-space-3, 12px);">
                ${gpus.map((gpu) => {
                  const util = gpu.utilizationPct ?? 0;
                  return html`
                    <div class="ring-card" style="padding: var(--ha-space-3, 12px); background: color-mix(in srgb, var(--unraid-text) 3%, transparent); border-radius: var(--ha-border-radius-md, 8px);">
                      <div style="display: flex; justify-content: space-between; align-items: center; margin-block-end: var(--ha-space-2, 8px); width: 100%;">
                        <div style="display: flex; align-items: center; gap: var(--ha-space-2, 8px);">
                          ${iconTemplate(mdiExpansionCard, 20)}
                          <span style="font-weight: var(--ha-font-weight-bold, 600); font-size: var(--ha-font-size-m, 14px);">${gpu.name}</span>
                        </div>
                        ${gpu.driver ? html`<span class="badge">${gpu.driver}</span>` : nothing}
                      </div>

                      <div class="rings-grid" style="grid-template-columns: repeat(auto-fit, minmax(90px, 1fr));">
                        ${gpu.utilizationPct !== undefined
                          ? html`
                              <button
                                type="button"
                                ?disabled=${!(gpu.utilizationEntityId)}
                                class="interactive ring-card"
                                @click=${() => gpu.utilizationEntityId && this.openMoreInfo(gpu.utilizationEntityId)}
                                title="Click for GPU load details"
                              >
                                <span data-block
                                  class="ring-gauge"
                                  style="--pct: ${util}; --ring-color: ${util > 80 ? "var(--unraid-error)" : util > 50 ? "var(--unraid-warning)" : "var(--unraid-online)"}"
                                >
                                  <span class="ring-content">${util}%</span>
                                </span>
                                <span class="ring-label">GPU Load</span>
                              </button>
                            `
                          : nothing}

                        ${gpu.temp !== undefined
                          ? html`
                              <button
                                type="button"
                                ?disabled=${!(gpu.tempEntityId)}
                                class="interactive ring-card"
                                @click=${() => gpu.tempEntityId && this.openMoreInfo(gpu.tempEntityId)}
                                title="Click for Temperature details"
                              >
                                <span data-block
                                  class="ring-gauge"
                                  style="--pct: ${Math.min(100, Math.round((gpu.temp / 90) * 100))}; --ring-color: ${gpu.temp > 80 ? "var(--unraid-error)" : gpu.temp > 65 ? "var(--unraid-warning)" : "var(--unraid-info)"}"
                                >
                                  <span class="ring-content">${gpu.temp}°C</span>
                                </span>
                                <span class="ring-label">Temperature</span>
                              </button>
                            `
                          : nothing}

                        ${gpu.power !== undefined
                          ? html`
                              <button
                                type="button"
                                ?disabled=${!(gpu.powerEntityId)}
                                class="interactive ring-card"
                                @click=${() => gpu.powerEntityId && this.openMoreInfo(gpu.powerEntityId)}
                                title="Click for Power details"
                              >
                                <span data-block class="ring-gauge" style="--pct: 60; --ring-color: var(--unraid-accent)">
                                  <span class="ring-content">${gpu.power}W</span>
                                </span>
                                <span class="ring-label">Power Draw</span>
                                ${gpu.energy !== undefined ? html`<span class="ring-subtext">${gpu.energy} kWh</span>` : nothing}
                              </button>
                            `
                          : nothing}

                        ${gpu.memUtilPct !== undefined
                          ? html`
                              <button
                                type="button"
                                ?disabled=${!(gpu.memUtilEntityId)}
                                class="interactive ring-card"
                                @click=${() => gpu.memUtilEntityId && this.openMoreInfo(gpu.memUtilEntityId)}
                                title="Click for VRAM details"
                              >
                                <span data-block class="ring-gauge" style="--pct: ${gpu.memUtilPct}; --ring-color: var(--unraid-info)">
                                  <span class="ring-content">${gpu.memUtilPct}%</span>
                                </span>
                                <span class="ring-label">VRAM Usage</span>
                              </button>
                            `
                          : nothing}
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
  tag: GPU_CARD_TAG,
  editorTag: GPU_EDITOR_TAG,
  card: UnraidGpuCard,
  editor: UnraidGpuCardEditor,
  name: "Unraid GPU Card",
  description: "Monitor graphics cards utilization, temperature, power draw, and VRAM",
});
