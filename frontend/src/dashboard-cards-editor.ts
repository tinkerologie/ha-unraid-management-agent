import { LitElement, css, html, nothing, type TemplateResult } from "lit";
import { type CardConfig } from "./config";
import { fireEvent, type HomeAssistant } from "./ha-types";

const labels: Record<string, string> = {
  server: "Unraid Management Agent server",
  title: "Custom title",
  view_mode: "Default view",
  show_system_info: "Show system details",
};

export class UnraidCardEditor extends LitElement {
  static override properties = {
    hass: { attribute: false },
    _config: { state: true },
  };

  declare hass?: HomeAssistant;
  declare _config?: CardConfig;

  static override styles = css`
    .card-config {
      display: flex;
      flex-direction: column;
      gap: var(--ha-space-4, 16px);
      padding-block: var(--ha-space-2, 8px);
      color: var(--primary-text-color);
    }
  `;

  private readonly _computeLabel = (schema: { name: string }): string =>
    labels[schema.name] ?? schema.name;

  private readonly _computeHelper = (schema: { name: string }): string | undefined =>
    schema.name === "server"
      ? "Only servers provided by Unraid Management Agent are listed."
      : undefined;

  setConfig(config: CardConfig): void {
    this._config = { ...config };
  }

  private _valueChanged(event: CustomEvent<{ value: Record<string, unknown> }>): void {
    event.stopPropagation();
    if (!this._config) return;
    const config = { ...this._config, ...event.detail.value };
    for (const key of ["server", "title"] as const) {
      if (config[key] === "") delete config[key];
    }
    this._config = config;
    fireEvent(this, "config-changed", { config });
  }

  protected override render(): TemplateResult {
    if (!this._config || !this.hass) return html``;
    const devices = Object.values(this.hass.devices ?? {}).filter(
      (device) =>
        !device.via_device_id && !device.parent_device_id &&
        device.identifiers?.some(([domain]) => domain === "unraid_management_agent")
    );
    const selected = this._config.server ? devices.find(
      (device) => device.id === this._config?.server ||
        device.name?.toLowerCase() === this._config?.server?.toLowerCase() ||
        device.name_by_user?.toLowerCase() === this._config?.server?.toLowerCase()
    ) : undefined;
    const server = selected?.id ?? this._config.server ?? "";
    const options = [
      { value: "", label: "Automatically select an Agent server" },
      ...devices.map((device) => ({
        value: device.id, label: device.name_by_user || device.name || device.id,
      })),
    ];
    if (server && !selected) {
      options.push({ value: server, label: `Unavailable Agent server: ${server}` });
    }
    const schema = [
      { name: "server", selector: { select: { options, mode: "dropdown" } } },
      { name: "title", selector: { text: {} } },
      ...(this._config.type.includes("docker")
        ? [{ name: "view_mode", selector: { select: { options: [
          { value: "grid", label: "Grid" }, { value: "list", label: "List" },
        ], mode: "dropdown" } } }]
        : []),
      ...(this._config.type.includes("server") || this._config.type.includes("dashboard")
        ? [{ name: "show_system_info", selector: { boolean: {} } }]
        : []),
    ];
    return html`
      <div class="card-config">
        ${devices.length === 0
          ? html`<ha-alert alert-type="info">No Unraid Management Agent server is available. Set up the integration to display its data.</ha-alert>`
          : nothing}
        <ha-form
          .hass=${this.hass}
          .schema=${schema}
          .data=${{ ...this._config, server, title: this._config.title ?? "",
            ...(schema.some((field) => field.name === "view_mode")
              ? { view_mode: this._config.view_mode ?? "grid" } : {}),
            ...(schema.some((field) => field.name === "show_system_info")
              ? { show_system_info: this._config.show_system_info !== false } : {}) }}
          .computeLabel=${this._computeLabel}
          .computeHelper=${this._computeHelper}
          @value-changed=${this._valueChanged}
        ></ha-form>
      </div>
    `;
  }
}

export class UnraidServerCardEditor extends UnraidCardEditor {}
export class UnraidStorageCardEditor extends UnraidCardEditor {}
export class UnraidSharesCardEditor extends UnraidCardEditor {}
export class UnraidNetworkCardEditor extends UnraidCardEditor {}
export class UnraidDockerCardEditor extends UnraidCardEditor {}
export class UnraidUpsCardEditor extends UnraidCardEditor {}
export class UnraidVmCardEditor extends UnraidCardEditor {}
export class UnraidZfsCardEditor extends UnraidCardEditor {}
export class UnraidFansCardEditor extends UnraidCardEditor {}
export class UnraidGpuCardEditor extends UnraidCardEditor {}
export class UnraidNotificationsCardEditor extends UnraidCardEditor {}
export class UnraidMaintenanceCardEditor extends UnraidCardEditor {}
export class UnraidRemoteSharesCardEditor extends UnraidCardEditor {}
export class UnraidUnassignedDevicesCardEditor extends UnraidCardEditor {}
export class UnraidDashboardCardEditor extends UnraidCardEditor {}
