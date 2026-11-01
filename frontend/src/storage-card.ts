import { html, nothing, type TemplateResult } from "lit";
import {
  STORAGE_CARD_TAG,
  STORAGE_EDITOR_TAG,
} from "./config";
import { BaseUnraidCard, formatFriendlyDateTime } from "./dashboard-cards-base";
import { UnraidStorageCardEditor } from "./dashboard-cards-editor";
import {
  iconTemplate,
  mdiAlertCircle,
  mdiCheckCircle,
  mdiHarddisk,
  mdiPlay,
  mdiShieldAlert,
  mdiShieldCheck,
  mdiStop,
  mdiUsbFlashDrive,
} from "./icons";
import { registerDashboardCard } from "./register-dashboard-card";

export type DiskHealthLevel = "healthy" | "warning" | "error" | "unknown";

export interface DiskItem {
  id: string;
  name: string;
  isParity: boolean;
  isCache: boolean;
  isBoot: boolean;
  usagePct: number;
  temp: string;
  tempNum?: number;
  errors: number;
  health: DiskHealthLevel;
  statusText?: string;
  isSpinning: boolean;
  spinEntityId?: string;
  freeSpace?: string;
  totalSpace?: string;
}

/** Read a disk's spin state from whichever attribute its entity exposes. */
function spinningFromAttributes(attrs: Record<string, unknown>): boolean | undefined {
  if (attrs.spin_state !== undefined) return attrs.spin_state === "active";
  if (attrs.spinning !== undefined) return Boolean(attrs.spinning);
  if (attrs.standby !== undefined) return !attrs.standby;
  return undefined;
}

/** Read a temperature that may be a number or text such as "41 °C". */
function parseTemperature(value: unknown): number | undefined {
  const parsed = typeof value === "number" ? value : parseFloat(String(value));
  return isNaN(parsed) ? undefined : parsed;
}

/** Map a disk health entity state (SMART text or binary sensor) to a level. */
function healthFromState(state: string): DiskHealthLevel {
  const clean = state.toLowerCase().trim();
  if (clean === "on" || clean.startsWith("fail")) return "error";
  if (["unknown", "unavailable", "none", ""].includes(clean)) return "unknown";
  return "healthy";
}

export function formatDiskName(rawName: string, id: string): string {
  const name = rawName.trim();
  const match = name.match(/^(?:.*?\s+)?(?:Disk\s+)?([a-zA-Z0-9_-]+)(?:\s+(?:usage|health|temperature|temp|spin|errors))?$/i);
  if (match && match[1]) {
    const token = match[1];
    const diskNum = token.match(/^disk[_\s]?(\d+)$/i);
    if (diskNum) return `Disk ${diskNum[1]}`;
    if (/^\d+$/.test(token)) return `Disk ${token}`;
    if (token.toLowerCase() === "parity") return "Parity";
    const parityNum = token.match(/^parity[_\s]?(\d+)$/i);
    if (parityNum) return `Parity ${parityNum[1]}`;
    if (token.toLowerCase() === "cache") return "Cache";
    if (token.toLowerCase().startsWith("cache_")) return `Cache (${token.slice(6).toUpperCase()})`;
    if (token.toLowerCase() === "boot" || token.toLowerCase() === "flash") return "Flash (Boot)";
    return token.replace(/\b\w/g, (c) => c.toUpperCase());
  }
  return name || id;
}

function extractDiskToken(entityId: string): string {
  const objectId = entityId.split(".")[1] || "";
  const token = objectId
    .replace(/^.*?_disk_/, "")
    .replace(/_usage$|_temperature$|_temp$|_errors$|_health$|_spin$/, "")
    .toLowerCase()
    .replace(/_/g, "");
  const numMatch = token.match(/^(?:disk)?(\d+)$/);
  if (numMatch) return `disk${numMatch[1]}`;
  return token;
}

export class UnraidStorageCard extends BaseUnraidCard {
  static override editorTag = STORAGE_EDITOR_TAG;

  private getDisks(): DiskItem[] {
    const usageEntities = this.getEntities("disk_usage");
    const healthEntities = this.getEntities("disk_health");
    const tempEntities = this.getEntities("disk_temperature");
    const errorEntities = this.getEntities("disk_error_count");
    const spinEntities = this.getEntities("disk_spin", "switch");

    const diskMap = new Map<string, DiskItem>();

    // 1. Process usage entities (Data and Cache disks)
    for (const u of usageEntities) {
      const diskKey = extractDiskToken(u.entity_id);
      const cleanName = formatDiskName((u.attributes.friendly_name as string) || diskKey, diskKey);
      const isParity = cleanName.toLowerCase().includes("parity");
      const isCache = cleanName.toLowerCase().includes("cache") || cleanName.toLowerCase().includes("pool");
      const isBoot = cleanName.toLowerCase().includes("boot") || cleanName.toLowerCase().includes("flash");

      const attrSpin = spinningFromAttributes(u.attributes) ?? false;
      const attrTemp = u.attributes.temperature_celsius ?? u.attributes.temperature;
      const attrErrors = Number(u.attributes.num_errors ?? 0);
      const attrStatus = (u.attributes.status as string) || "DISK_OK";

      diskMap.set(diskKey, {
        id: diskKey,
        name: cleanName,
        isParity,
        isCache,
        isBoot,
        usagePct: Math.round(Number(u.state) || 0),
        temp: attrTemp !== undefined && attrTemp !== null ? `${attrTemp}°C` : "*",
        tempNum: typeof attrTemp === "number" ? attrTemp : undefined,
        errors: attrErrors,
        health: "healthy",
        statusText: attrStatus,
        isSpinning: attrSpin,
        freeSpace: u.attributes.free as string | undefined,
        totalSpace: u.attributes.total as string | undefined,
      });
    }

    // 2. Add any disks from healthEntities not yet in diskMap (e.g. Parity disk)
    for (const h of healthEntities) {
      const diskKey = extractDiskToken(h.entity_id);
      if (diskMap.has(diskKey)) continue;
      // Unraid reports an empty slot as DISK_NP or DISK_NP_DSBL.
      if (/^disk_np/i.test(h.state)) continue;
      if (diskKey.includes("disabled") || diskKey.includes("missing") || diskKey.includes("invalid")) continue;

      const cleanName = formatDiskName((h.attributes.friendly_name as string) || diskKey, diskKey);
      const isParity = cleanName.toLowerCase().includes("parity");
      const isCache = cleanName.toLowerCase().includes("cache");
      const isBoot = cleanName.toLowerCase().includes("boot");
      const attrSpin = spinningFromAttributes(h.attributes) ?? false;
      const attrTemp = parseTemperature(h.attributes.temperature);
      const attrStatus = (h.attributes.status as string) || "DISK_OK";

      diskMap.set(diskKey, {
        id: diskKey,
        name: cleanName,
        isParity,
        isCache,
        isBoot,
        usagePct: 0,
        temp: attrTemp !== undefined && attrTemp !== null ? `${attrTemp}°C` : "*",
        tempNum: typeof attrTemp === "number" ? attrTemp : undefined,
        errors: 0,
        health: healthFromState(h.state),
        statusText: attrStatus,
        isSpinning: attrSpin,
      });
    }

    // 3. Match dedicated temperature entities
    for (const t of tempEntities) {
      const key = extractDiskToken(t.entity_id);
      const disk = diskMap.get(key);
      if (disk && t.state !== "unavailable" && t.state !== "unknown") {
        disk.temp = `${t.state}°C`;
        disk.tempNum = parseFloat(t.state);
      }
    }

    // 4. Match error sensors
    for (const e of errorEntities) {
      const key = extractDiskToken(e.entity_id);
      const disk = diskMap.get(key);
      if (disk) {
        const val = Number(e.state);
        if (!isNaN(val)) disk.errors = val;
      }
    }

    // 5. Match spin switches
    for (const s of spinEntities) {
      const key = extractDiskToken(s.entity_id);
      const disk = diskMap.get(key);
      if (disk) {
        disk.isSpinning = s.state === "on";
        disk.spinEntityId = s.entity_id;
      }
    }

    // 6. Match health binary sensors & resolve health level
    for (const h of healthEntities) {
      const key = extractDiskToken(h.entity_id);
      const disk = diskMap.get(key);
      if (disk) {
        if (h.attributes.status) {
          disk.statusText = h.attributes.status as string;
        }
        disk.isSpinning = spinningFromAttributes(h.attributes) ?? disk.isSpinning;
        const healthTemp = parseTemperature(h.attributes.temperature);
        if (healthTemp !== undefined && disk.temp === "*") {
          disk.temp = `${healthTemp}°C`;
          disk.tempNum = healthTemp;
        }
        disk.health = healthFromState(h.state);
      }
    }

    // 7. Calculate overall health level
    for (const disk of diskMap.values()) {
      const status = (disk.statusText || "").toUpperCase();
      const hasStatusError = status.includes("ERR") || status.includes("WRONG") || status.includes("INVALID") || status.includes("DSBL") || status.includes("FAIL");

      if (disk.health === "error" || hasStatusError || disk.errors >= 10) {
        disk.health = "error";
      } else if (disk.errors > 0 || (disk.tempNum !== undefined && disk.tempNum > 45)) {
        disk.health = "warning";
      } else if (disk.health !== "unknown") {
        disk.health = "healthy";
      }
    }

    return Array.from(diskMap.values()).sort((a, b) => {
      if (a.isParity !== b.isParity) {
        return a.isParity ? -1 : 1;
      }
      if (a.isBoot !== b.isBoot) {
        return a.isBoot ? 1 : -1;
      }
      if (a.isCache !== b.isCache) {
        return a.isCache ? 1 : -1;
      }
      return a.name.localeCompare(b.name, undefined, { numeric: true });
    });
  }

  private isUsable(entity?: { state?: string } | null): boolean {
    if (!entity || !entity.state) return false;
    const s = entity.state.toLowerCase().trim();
    return s !== "unavailable" && s !== "unknown" && s !== "none" && s !== "--";
  }

  private getParityViewState(): {
    validity: "valid" | "invalid" | "unknown";
    activity: "idle" | "running" | "paused" | "unknown";
    progressPct: number;
  } {
    const parityValid = this.getEntity("parity_valid", "binary_sensor");
    const parityRunning = this.getEntity("parity_check_running", "binary_sensor");
    const legacyParityStatus =
      this.getEntity("parity_status", "binary_sensor") ?? this.getEntity("parity_status");
    const parityProgress = this.getEntity("parity_progress");

    // Validity: binary_sensor.parity_valid has device_class problem (off = valid, on = invalid)
    let validity: "valid" | "invalid" | "unknown" = "unknown";
    if (this.isUsable(parityValid)) {
      const s = parityValid!.state.toLowerCase().trim();
      if (s === "off") {
        validity = "valid";
      } else if (s === "on") {
        validity = "invalid";
      }
    } else if (this.isUsable(legacyParityStatus)) {
      const s = legacyParityStatus!.state.toLowerCase().trim();
      if (s === "off") {
        validity = "valid";
      } else if (s === "on") {
        const st = String(legacyParityStatus!.attributes?.status ?? "").toLowerCase().trim();
        if (st !== "running" && st !== "paused") {
          validity = "invalid";
        }
      }
    }

    // Activity: binary_sensor.parity_check_running has device_class running (on = active, off = idle)
    let activity: "idle" | "running" | "paused" | "unknown" = "unknown";
    if (this.isUsable(parityRunning)) {
      const s = parityRunning!.state.toLowerCase().trim();
      if (s === "off") {
        activity = "idle";
      } else if (s === "on") {
        const st = String(parityRunning!.attributes?.status ?? "").toLowerCase().trim();
        activity = st === "paused" ? "paused" : "running";
      }
    } else if (this.isUsable(legacyParityStatus)) {
      const st = String(legacyParityStatus!.attributes?.status ?? "").toLowerCase().trim();
      if (st === "running") {
        activity = "running";
      } else if (st === "paused") {
        activity = "paused";
      } else if (legacyParityStatus!.state.toLowerCase().trim() === "off") {
        activity = "idle";
      }
    }

    // Progress: only used for display percentage when numeric
    let progressPct = 0;
    if (this.isUsable(parityProgress)) {
      const val = Number(parityProgress!.state);
      if (!isNaN(val)) {
        progressPct = Math.round(val);
      }
    }

    return { validity, activity, progressPct };
  }

  protected override render(): TemplateResult {
    const arrayUsage = this.getEntity("array_usage");
    const paritySwitch = this.getEntity("parity_check", "switch");
    const lastCheckDate = this.getEntity("last_parity_check_date") || this.getEntity("last_parity_check");
    const lastCheckErrors = this.getEntity("last_parity_check_errors");

    const arrayPct = Math.round(Number(arrayUsage?.state) || 0);
    const usedStr = (arrayUsage?.attributes?.capacity_used as string) || "";
    const totalStr = (arrayUsage?.attributes?.capacity_total as string) || "";
    const freeStr = (arrayUsage?.attributes?.capacity_free as string) || "";

    const { validity, activity, progressPct } = this.getParityViewState();
    const isChecking = activity === "running" || activity === "paused";

    let badgeClass = "badge-standby";
    let badgeText = "Parity Status Unknown";
    let badgeIcon = mdiShieldAlert;
    if (validity === "valid") {
      badgeClass = "badge-online";
      badgeText = "Parity Valid";
      badgeIcon = mdiShieldCheck;
    } else if (validity === "invalid") {
      badgeClass = "badge-warning";
      badgeText = "Parity Check Needed";
      badgeIcon = mdiShieldAlert;
    }

    const disks = this.getDisks();

    const badge = html`
      <span class="badge ${badgeClass}">
        ${iconTemplate(badgeIcon, 13)}
        <span>${badgeText}</span>
      </span>
    `;

    let parityTitle: string;
    if (activity === "running") {
      parityTitle = `Parity Check In Progress (${progressPct}%)`;
    } else if (activity === "paused") {
      parityTitle = `Parity Check Paused (${progressPct}%)`;
    } else if (validity === "valid") {
      parityTitle = "Parity Status: Valid";
    } else if (validity === "invalid") {
      parityTitle = "Parity Status: Check Needed";
    } else {
      parityTitle = "Parity Status: Unknown";
    }

    const rowIcon = validity === "valid" || isChecking ? mdiCheckCircle : mdiAlertCircle;
    const rowColor =
      validity === "valid" || isChecking ? "var(--unraid-online)" : "var(--unraid-warning)";

    const hasLastCheckDate = this.isUsable(lastCheckDate);
    const numErrors = Number(lastCheckErrors?.state);
    const hasErrors =
      this.isUsable(lastCheckErrors) && !isNaN(numErrors) && numErrors > 0;

    let historyText = "";
    if (hasLastCheckDate) {
      const resultSuffix =
        lastCheckDate!.attributes?.result && lastCheckDate!.attributes.result !== "Completed"
          ? ` (${lastCheckDate!.attributes.result})`
          : "";
      historyText = `Last check: ${formatFriendlyDateTime(lastCheckDate!.state)}${resultSuffix}`;
    } else if (validity === "valid") {
      historyText = "Parity healthy";
    }
    const errorsText = hasErrors ? ` • ${lastCheckErrors!.state} errors` : "";
    const showHistoryLine = Boolean(historyText || errorsText);

    return html`
      <ha-card>
        ${this.renderHeader(
          this.config.title || "Storage Array & Disks",
          `${usedStr || `${arrayPct}%`} used of ${totalStr || "Array"}${freeStr ? ` (${freeStr} Free)` : ""}`,
          mdiHarddisk,
          badge
        )}
        <div style="display: flex; flex-direction: column; gap: var(--ha-space-1, 4px);">
          <div style="display: flex; justify-content: space-between; font-size: var(--ha-font-size-s, 12px); font-weight: var(--ha-font-weight-bold, 600);">
            <span>Array Capacity</span>
            <span>${arrayPct}%</span>
          </div>
          <div class="progress-bar">
            <div class="progress-fill" style="width: ${arrayPct}%;"></div>
          </div>
        </div>
        <div class="list-row" style="background: color-mix(in srgb, var(--unraid-text) 5%, transparent);">
          <div class="row-left">
            <div style="color: ${rowColor}">
              ${iconTemplate(rowIcon, 18)}
            </div>
            <div style="display: flex; flex-direction: column; min-width: 0;">
              <span style="font-weight: var(--ha-font-weight-bold, 600); font-size: var(--ha-font-size-s, 12px);">
                ${parityTitle}
              </span>
              ${showHistoryLine
                ? html`
                    <span style="font-size: var(--ha-font-size-s, 12px); color: var(--unraid-subtext);">
                      ${historyText}${errorsText}
                    </span>
                  `
                : nothing}
            </div>
          </div>
          <div class="row-right">
            ${paritySwitch
              ? html`
                  <button
                    class="btn ${isChecking ? "btn" : "btn-primary"}"
                    @click=${() => this.toggleEntity(paritySwitch.entity_id)}
                  >
                    ${iconTemplate(isChecking ? mdiStop : mdiPlay, 14)}
                    <span>${isChecking ? "Cancel" : "Check Now"}</span>
                  </button>
                `
              : nothing}
          </div>
        </div>
        <div class="item-list">
          ${disks.length > 0
            ? disks.map((disk) => {
                const tempNum = disk.tempNum ?? parseFloat(disk.temp);
                const hasValidTemp = disk.isSpinning && !isNaN(tempNum) && disk.temp !== "*" && disk.temp !== "unavailable";
                const tempColor = hasValidTemp
                  ? tempNum > 45
                    ? "var(--unraid-error)"
                    : tempNum > 36
                    ? "var(--unraid-warning)"
                    : "var(--unraid-online)"
                  : "var(--unraid-standby)";

                const tempDisplay = hasValidTemp ? `${Math.round(tempNum)}°C` : "--";

                const healthBadge = disk.health === "unknown"
                  ? html`
                      <span
                        class="badge badge-standby"
                        style="font-size: var(--ha-font-size-s, 12px);"
                        title="SMART status can't be read, usually because the disk is spun down"
                      >
                        <span>Unknown</span>
                      </span>
                    `
                  : disk.health === "healthy"
                  ? html`
                      <span class="badge badge-online" style="font-size: var(--ha-font-size-s, 12px); gap: var(--ha-space-1, 4px);">
                        ${iconTemplate(mdiCheckCircle, 11)}
                        <span>Healthy</span>
                      </span>
                    `
                  : disk.health === "warning"
                  ? html`
                      <span class="badge badge-warning" style="font-size: var(--ha-font-size-s, 12px); gap: var(--ha-space-1, 4px);">
                        ${iconTemplate(mdiAlertCircle, 11)}
                        <span>Warning${disk.errors > 0 ? ` (${disk.errors})` : ""}</span>
                      </span>
                    `
                  : html`
                      <span class="badge badge-error" style="font-size: var(--ha-font-size-s, 12px); gap: var(--ha-space-1, 4px);">
                        ${iconTemplate(mdiAlertCircle, 11)}
                        <span>Error${disk.errors > 0 ? ` (${disk.errors})` : ""}</span>
                      </span>
                    `;

                return html`
                  <div class="list-row">
                    <div class="row-left">
                      ${disk.isBoot
                        ? html`
                            <span
                              class="badge badge-online"
                              style="font-size: var(--ha-font-size-s, 12px); gap: var(--ha-space-1, 4px); min-width: 60px; justify-content: center;"
                              title="USB Flash Boot Drive"
                            >
                              ${iconTemplate(mdiUsbFlashDrive, 11)}
                              <span>Flash</span>
                            </span>
                          `
                        : disk.spinEntityId
                        ? html`
                            <button
                              class="badge ${disk.isSpinning ? "badge-online" : "badge-standby"}"
                              style="cursor: pointer; border: none;"
                              title="Click to spin ${disk.isSpinning ? "down" : "up"}"
                              @click=${() => this.toggleEntity(disk.spinEntityId!)}
                            >
                              <span class="status-dot ${disk.isSpinning ? "online" : "offline"}"></span>
                              <span>${disk.isSpinning ? "Active" : "Standby"}</span>
                            </button>
                          `
                        : html`
                            <span class="badge ${disk.isSpinning ? "badge-online" : "badge-standby"}">
                              <span>${disk.isSpinning ? "Active" : "Standby"}</span>
                            </span>
                          `}

                      <span style="font-weight: var(--ha-font-weight-bold, 600); min-width: 75px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
                        ${disk.name}
                      </span>
                    </div>

                    <div class="row-right">
                      <span
                        class="badge"
                        style="color: ${disk.isBoot ? "var(--unraid-subtext)" : tempColor}; background: color-mix(in srgb, ${disk.isBoot ? "var(--unraid-subtext)" : tempColor} 12%, transparent); min-width: 44px; justify-content: center;"
                        title="${disk.isBoot ? "USB Flash Drive" : disk.isSpinning ? `Temperature: ${tempDisplay}` : "Disk is in standby"}"
                      >
                        ${disk.isBoot ? "--" : tempDisplay}
                      </span>
                      ${healthBadge}
                      <div style="display: flex; align-items: center; gap: var(--ha-space-2, 8px); width: 85px;">
                        ${disk.isParity
                          ? html`
                              <span style="font-size: var(--ha-font-size-s, 12px); color: var(--unraid-online); font-weight: var(--ha-font-weight-medium, 500); font-family: var(--ha-font-family-code, monospace);">
                                Parity
                              </span>
                            `
                          : html`
                              <div class="progress-bar" style="height: 4px; flex: 1;">
                                <div
                                  class="progress-fill"
                                  style="width: ${disk.usagePct}%; background: ${disk.isBoot ? "var(--unraid-warning)" : disk.isCache ? "var(--unraid-info)" : "var(--unraid-accent)"};"
                                ></div>
                              </div>
                              <span style="font-size: var(--ha-font-size-s, 12px); font-family: var(--ha-font-family-code, monospace); color: var(--unraid-subtext);">
                                ${disk.usagePct}%
                              </span>
                            `}
                      </div>
                    </div>
                  </div>
                `;
              })
            : html`<div style="text-align: center; color: var(--unraid-subtext); font-size: var(--ha-font-size-s, 12px); padding: var(--ha-space-3, 12px);">No disk devices found</div>`}
        </div>
      </ha-card>
    `;
  }
}

registerDashboardCard({
  tag: STORAGE_CARD_TAG,
  editorTag: STORAGE_EDITOR_TAG,
  card: UnraidStorageCard,
  editor: UnraidStorageCardEditor,
  name: "Unraid Storage & Disks Card",
  description: "Array capacity, parity checks, and interactive disk tray with spin state controls.",
});
