export interface HassEntity {
  entity_id: string;
  state: string;
  attributes: Record<string, unknown>;
  last_changed: string;
  last_updated: string;
}

export type HassEntities = Record<string, HassEntity>;

export interface DeviceRegistryEntry {
  id: string;
  name: string;
  name_by_user?: string | null;
  identifiers: [string, string][];
  manufacturer?: string | null;
  model?: string | null;
  sw_version?: string | null;
  hw_version?: string | null;
  /** Set on the Docker and VMs devices, linking them to their server device */
  via_device_id?: string | null;
  /** Set on child devices (containers, VMs, GPUs, storage) of another device */
  parent_device_id?: string | null;
}

export interface EntityRegistryEntry {
  entity_id: string;
  device_id?: string | null;
  platform?: string;
  translation_key?: string;
  original_name?: string;
  name?: string | null;
}

/** Full registry records also include disabled entities absent from states. */
export interface FullEntityRegistryEntry extends EntityRegistryEntry {
  unique_id: string;
  config_entry_id: string | null;
  disabled_by: string | null;
}

export interface HomeAssistant {
  callWS?: <T>(message: { type: string }) => Promise<T>;
  /** HA display-name API; validate its result at runtime. */
  formatEntityName?: (entity: HassEntity) => unknown;
  states: HassEntities;
  devices?: Record<string, DeviceRegistryEntry>;
  entities?: Record<string, EntityRegistryEntry>;
  callService: (
    domain: string,
    service: string,
    serviceData?: Record<string, unknown>
  ) => Promise<unknown>;
}

export function fireEvent(
  node: HTMLElement | Window,
  type: string,
  detail?: unknown,
  options?: { bubbles?: boolean; cancelable?: boolean; composed?: boolean }
): Event {
  const event = new CustomEvent(type, {
    bubbles: options?.bubbles ?? true,
    cancelable: Boolean(options?.cancelable),
    composed: options?.composed ?? true,
    detail,
  });
  node.dispatchEvent(event);
  return event;
}
