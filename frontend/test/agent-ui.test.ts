import { afterEach, describe, expect, it, vi } from "vitest";
import "../src/index";
import { UnraidDockerCard } from "../src/docker-card";
import { UnraidDashboardCard } from "../src/dashboard-card";
import {
  UnraidDashboardCardEditor,
  UnraidDockerCardEditor,
  UnraidServerCardEditor,
  UnraidSharesCardEditor,
} from "../src/dashboard-cards-editor";
import type { HomeAssistant } from "../src/ha-types";

// Exercise the card's HA-dialog bindings and events without importing HA's
// application bundle. The native dialog fallback is covered in Chromium.
customElements.define("ha-dialog", class extends HTMLElement {
  open = false;
  headerTitle = "";
  preventScrimClose = false;
});

const containerId = "switch.agent_container_plex";
const restartId = "button.agent_container_restart_plex";

function agentHass(): HomeAssistant {
  return {
    devices: {
      agent: { id: "agent", name: "Agent", identifiers: [["unraid_management_agent", "agent"]] },
      foreign: { id: "foreign", name: "Other", identifiers: [["unraid", "other"]] },
    },
    states: {
      [containerId]: { entity_id: containerId, state: "on", attributes: { friendly_name: "Agent Container plex" }, last_changed: "", last_updated: "" },
      [restartId]: { entity_id: restartId, state: "unknown", attributes: {}, last_changed: "", last_updated: "" },
    },
    entities: {
      [containerId]: { entity_id: containerId, device_id: "agent", platform: "unraid_management_agent", translation_key: "docker_container" },
      [restartId]: { entity_id: restartId, device_id: "agent", platform: "unraid_management_agent", translation_key: "docker_container_restart" },
    },
    callService: vi.fn(async () => undefined),
  };
}

async function dockerCard(hass = agentHass()) {
  const card = new UnraidDockerCard();
  card.setConfig({ type: "custom:unraid-management-agent-docker-card", server: "agent" });
  card.hass = hass;
  document.body.append(card);
  await card.updateComplete;
  return card;
}

function button(card: UnraidDockerCard, label: string): HTMLButtonElement {
  const match = [...card.shadowRoot!.querySelectorAll<HTMLButtonElement>("button")].find(
    (element) => element.getAttribute("aria-label") === label || element.textContent?.trim() === label
  );
  expect(match, `Button ${label}`).toBeDefined();
  return match!;
}

async function openStop(card: UnraidDockerCard) {
  button(card, "Stop plex").click();
  await card.updateComplete;
  return card.shadowRoot!.querySelector("ha-dialog") as HTMLElement & { open: boolean; headerTitle: string; preventScrimClose: boolean };
}

async function confirm(card: UnraidDockerCard) {
  card.shadowRoot!.querySelector<HTMLButtonElement>("ha-dialog .btn-danger")!.click();
  await card.updateComplete;
}

afterEach(() => {
  document.body.replaceChildren();
  vi.restoreAllMocks();
});

describe("Agent container action boundaries", () => {
  it("does not dispatch when hass is missing or an action is already pending", async () => {
    const hass = agentHass();
    const card = new UnraidDockerCard() as any;
    await card.runContainerAction(containerId, "start");
    expect(card._busy).toBe(false);
    card.hass = hass;
    card._busy = true;
    await card.runContainerAction(containerId, "start");
    expect(hass.callService).not.toHaveBeenCalled();
  });

  it("rechecks ownership when a user accepts an already-open confirmation", async () => {
    const hass = agentHass();
    const card = await dockerCard(hass);
    const dialog = await openStop(card);
    expect(dialog.open).toBe(true);
    card.hass = {
      ...hass,
      entities: { ...hass.entities, [containerId]: { entity_id: containerId, device_id: "agent", platform: "unraid" } },
    };
    await card.updateComplete;
    await confirm(card);
    expect(hass.callService).not.toHaveBeenCalled();
    expect(dialog.open).toBe(false);
    expect(card.shadowRoot!.querySelector('[role="alert"]')?.textContent).toContain("no longer available");
  });

  it("starts a stopped owned container directly without a confirmation", async () => {
    const hass = agentHass();
    hass.states[containerId]!.state = "off";
    const card = await dockerCard(hass);
    button(card, "Start plex").click();
    await vi.waitFor(() => expect(hass.callService).toHaveBeenCalledExactlyOnceWith("switch", "turn_on", { entity_id: containerId }));
    await card.updateComplete;
    expect((card.shadowRoot!.querySelector("ha-dialog") as any).open).toBe(false);
  });

  it("cancels the HA dialog without a call and prevents duplicate in-flight actions", async () => {
    const hass = agentHass();
    let finish!: () => void;
    hass.callService = vi.fn(() => new Promise<void>((resolve) => { finish = resolve; }));
    const card = await dockerCard(hass);
    const dialog = await openStop(card);
    expect(dialog.headerTitle).toBe("Stop container?");
    button(card, "Cancel").click();
    await card.updateComplete;
    expect(dialog.open).toBe(false);
    expect(hass.callService).not.toHaveBeenCalled();
    await openStop(card);
    await confirm(card);
    expect(dialog.preventScrimClose).toBe(true);
    expect(card.shadowRoot!.querySelector<HTMLButtonElement>("ha-dialog .btn-danger")!.disabled).toBe(true);
    await (card as any).runContainerAction(containerId, "stop");
    expect(hass.callService).toHaveBeenCalledExactlyOnceWith("switch", "turn_off", { entity_id: containerId });
    finish();
    await vi.waitFor(() => expect((card as any)._busy).toBe(false));
    await card.updateComplete;
    expect(dialog.open).toBe(false);
  });

  it("shows HA-dialog service errors and handles user dismissal", async () => {
    const hass = agentHass();
    hass.callService = vi.fn(async () => { throw new Error("offline"); });
    const card = await dockerCard(hass);
    const dialog = await openStop(card);
    await confirm(card);
    await vi.waitFor(() => expect((card as any)._busy).toBe(false));
    await card.updateComplete;
    expect(dialog.open).toBe(true);
    expect(dialog.querySelector('[role="alert"]')?.textContent).toContain("action failed");
    dialog.dispatchEvent(new CustomEvent("closed"));
    await card.updateComplete;
    expect(dialog.open).toBe(false);
  });

  it("confirms HA-dialog restarts against the owned restart button", async () => {
    const hass = agentHass();
    const card = await dockerCard(hass);
    button(card, "Restart plex").click();
    await card.updateComplete;
    expect((card.shadowRoot!.querySelector("ha-dialog") as any).headerTitle).toBe("Restart container?");
    await confirm(card);
    expect(hass.callService).toHaveBeenCalledExactlyOnceWith("button", "press", { entity_id: restartId });
  });
});

describe("Agent native editor states", () => {
  it("renders no form until both configuration and hass are supplied", async () => {
    const editor = new UnraidSharesCardEditor();
    document.body.append(editor);
    await editor.updateComplete;
    expect(editor.shadowRoot!.querySelector("ha-form")).toBeNull();
    editor.setConfig({ type: "custom:unraid-management-agent-shares-card" });
    await editor.updateComplete;
    expect(editor.shadowRoot!.querySelector("ha-form")).toBeNull();
  });

  it("explains missing Agent roots and retains an unavailable explicit server", async () => {
    const editor = new UnraidSharesCardEditor();
    const hass = agentHass();
    editor.hass = { ...hass, devices: { foreign: hass.devices!.foreign! } };
    editor.setConfig({ type: "custom:unraid-management-agent-shares-card", server: "missing" });
    document.body.append(editor);
    await editor.updateComplete;
    expect(editor.shadowRoot!.querySelector("ha-alert")?.textContent).toContain("No Unraid Management Agent server");
    const form = editor.shadowRoot!.querySelector("ha-form") as any;
    expect(form.data.server).toBe("missing");
    expect(form.schema[0].selector.select.options).toEqual([
      { value: "", label: "Automatically select an Agent server" },
      { value: "missing", label: "Unavailable Agent server: missing" },
    ]);
    expect(form.computeHelper({ name: "server" })).toContain("Only servers provided by Unraid Management Agent");
    expect(form.computeHelper({ name: "title" })).toBeUndefined();
    expect(form.computeLabel({ name: "custom_field" })).toBe("custom_field");
    expect(UnraidDockerCard.getStubConfig(editor.hass)).toEqual({});
    expect(UnraidDockerCard.getStubConfig()).toEqual({});
  });

  it.each([
    [UnraidDockerCardEditor, "docker", { view_mode: "grid" }],
    [UnraidServerCardEditor, "server", { show_system_info: true }],
    [UnraidDashboardCardEditor, "dashboard", { show_system_info: true }],
    [UnraidSharesCardEditor, "shares", {}],
  ] as const)("supplies defaults only for the %s editor's active schema", async (Editor, module, defaults) => {
    const editor = new Editor();
    editor.hass = agentHass();
    editor.setConfig({ type: `custom:unraid-management-agent-${module}-card` });
    document.body.append(editor);
    await editor.updateComplete;
    const form = editor.shadowRoot!.querySelector("ha-form") as any;
    expect(form.data).toEqual({ type: `custom:unraid-management-agent-${module}-card`, server: "", title: "", ...defaults });
    expect(form.schema.map((field: any) => field.name)).toEqual(["server", "title", ...Object.keys(defaults)]);
    if (module === "docker") {
      expect(form.schema[2].selector.select.options.map((option: any) => option.value)).toEqual(["grid", "list"]);
      editor.setConfig({ type: "custom:unraid-management-agent-docker-card", view_mode: "list" });
      await editor.updateComplete;
      expect((editor.shadowRoot!.querySelector("ha-form") as any).data.view_mode).toBe("list");
    } else if ("show_system_info" in defaults) {
      editor.setConfig({ type: `custom:unraid-management-agent-${module}-card`, show_system_info: false });
      await editor.updateComplete;
      expect((editor.shadowRoot!.querySelector("ha-form") as any).data.show_system_info).toBe(false);
    }
  });
});

it("uses the Agent tag, server and selected-state semantics for every embedded tab", async () => {
  const dashboard = new UnraidDashboardCard();
  dashboard.hass = agentHass();
  dashboard.setConfig({ type: "custom:unraid-management-agent-dashboard-card", server: "agent" });
  document.body.append(dashboard);
  await dashboard.updateComplete;
  for (const [label, module] of [
    ["Overview", "server"], ["Storage", "storage"], ["ZFS", "zfs"], ["Shares", "shares"],
    ["Remote", "remote-shares"], ["Unassigned", "unassigned-devices"], ["Network", "network"],
    ["Docker", "docker"], ["VMs", "vm"], ["Fans", "fans"], ["GPU", "gpu"], ["UPS", "ups"],
    ["Maintenance", "maintenance"], ["Notifications", "notifications"],
  ]) {
    const tab = [...dashboard.shadowRoot!.querySelectorAll<HTMLButtonElement>(".tab-btn")].find((element) => element.textContent?.trim() === label)!;
    tab.click();
    await dashboard.updateComplete;
    const child = dashboard.shadowRoot!.querySelector(`unraid-management-agent-${module}-card`) as any;
    expect(child, label).not.toBeNull();
    expect(child.config).toMatchObject({ type: `custom:unraid-management-agent-${module}-card`, server: "agent", embedded: true });
    expect(tab.getAttribute("aria-pressed")).toBe("true");
    expect(dashboard.shadowRoot!.querySelectorAll('.tab-btn[aria-pressed="true"]')).toHaveLength(1);
  }
});
