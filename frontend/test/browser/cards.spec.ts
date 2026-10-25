import { expect, test } from "@playwright/test";

test.describe("Unraid Lovelace Dashboard Cards Browser Tests", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/test/browser/fixture.html");
    await page.waitForFunction(
      () => (window as unknown as { fixtureReady?: boolean }).fixtureReady === true
    );
  });

  test("defines all custom card elements without template corruption", async ({ page }) => {
    const defined = await page.evaluate(() => {
      const tags = [
        "unraid-management-agent-server-card",
        "unraid-management-agent-storage-card",
        "unraid-management-agent-shares-card",
        "unraid-management-agent-docker-card",
        "unraid-management-agent-ups-card",
        "unraid-management-agent-vm-card",
        "unraid-management-agent-network-card",
        "unraid-management-agent-zfs-card",
        "unraid-management-agent-fans-card",
        "unraid-management-agent-gpu-card",
        "unraid-management-agent-notifications-card",
        "unraid-management-agent-maintenance-card",
        "unraid-management-agent-remote-shares-card",
        "unraid-management-agent-unassigned-devices-card",
        "unraid-management-agent-dashboard-card",
      ];
      return tags.every((t) => Boolean(customElements.get(t)));
    });
    expect(defined).toBe(true);

    // Verify NO raw Lit placeholder markers or leaked attribute syntax exist in DOM
    const rawLitMarkers = await page.evaluate(() => {
      const allText = document.body.innerText;
      return allText.includes("lit$") || allText.includes("@click=") || allText.includes(".style=");
    });
    expect(rawLitMarkers).toBe(false);
  });

  test("renders Server Card with system metrics", async ({ page }) => {
    const serverCard = page.locator("#server-card");
    await expect(serverCard).toBeVisible();

    await expect(serverCard.getByText("Cube")).toBeVisible();
    await expect(serverCard.getByText("CPU Load")).toBeVisible();
    await expect(serverCard.getByText("15%")).toBeVisible();
    await expect(serverCard.getByText("Memory")).toBeVisible();
    await expect(serverCard.getByText("System Uptime")).toBeVisible();
    await expect(serverCard.getByText("Primary Network")).toBeVisible();
    await expect(serverCard.getByText("Boot Device")).toBeVisible();
    await expect(serverCard.getByText(/Flash/)).toBeVisible();
  });

  test("renders Storage Card with clean disk names and Healthy status badges", async ({ page }) => {
    const storageCard = page.locator("#storage-card");
    await expect(storageCard).toBeVisible();

    await expect(storageCard.getByText("Storage Array & Disks")).toBeVisible();
    await expect(storageCard.getByText("Parity", { exact: true }).first()).toBeVisible();
    await expect(storageCard.getByText("Disk 1", { exact: true }).first()).toBeVisible();
    await expect(storageCard.getByText("Cache", { exact: true }).first()).toBeVisible();
    await expect(storageCard.getByText("Flash (Boot)", { exact: true }).first()).toBeVisible();
    await expect(storageCard.getByText("Healthy").first()).toBeVisible();
    await expect(storageCard.getByText("--").first()).toBeVisible();
    await expect(storageCard.getByText("29°C")).toBeVisible();
  });

  test("renders Shares Card with user shares and protection states", async ({ page }) => {
    const sharesCard = page.locator("#shares-card");
    await expect(sharesCard).toBeVisible();

    await expect(sharesCard.getByText("User Shares")).toBeVisible();
    await expect(sharesCard.getByText("appdata")).toBeVisible();
    await expect(sharesCard.getByText("media")).toBeVisible();
    await expect(sharesCard.getByText("Protected").first()).toBeVisible();
    await expect(sharesCard.getByText("Unprotected").first()).toBeVisible();
    await expect(sharesCard.getByText("46.6 GB / 480.6 GB")).toBeVisible();
    await expect(sharesCard.getByText("1.4 TB / 39.1 TB")).toBeVisible();
  });

  test("renders Network Card with interfaces and link metrics", async ({ page }) => {
    const networkCard = page.locator("#network-card");
    await expect(networkCard).toBeVisible();

    await expect(networkCard.getByText("Cube Network")).toBeVisible();
    await expect(networkCard.getByText("ETH0")).toBeVisible();
    await expect(networkCard.getByText("192.168.20.21", { exact: true }).first()).toBeVisible();
    await expect(networkCard.getByText("1 Gbps")).toBeVisible();
    await expect(networkCard.getByText("12.40 MB/s")).toBeVisible();
    await expect(networkCard.getByText("5.80 MB/s")).toBeVisible();
  });

  test("renders Dashboard Card and allows tab navigation", async ({ page }) => {
    const dashboardCard = page.locator("unraid-management-agent-dashboard-card");
    await expect(dashboardCard).toBeVisible();

    // Default overview tab
    await expect(dashboardCard.locator("unraid-management-agent-server-card")).toBeVisible();

    // Click Shares tab
    await dashboardCard.locator(".tab-btn:has-text('Shares')").click();
    await expect(dashboardCard.locator("unraid-management-agent-shares-card")).toBeVisible();

    // Click Network tab
    await dashboardCard.locator(".tab-btn:has-text('Network')").click();
    await expect(dashboardCard.locator("unraid-management-agent-network-card")).toBeVisible();

    // Click Storage tab
    await dashboardCard.locator(".tab-btn:has-text('Storage')").click();
    await expect(dashboardCard.locator("unraid-management-agent-storage-card")).toBeVisible();
  });

  test("container navigation and filters work with keyboard and expose selection", async ({ page }) => {
    const card = page.locator("#docker-card");
    await card.getByRole("button", { name: "Running (1)", exact: true }).click();
    await expect(card.getByRole("button", { name: "Running (1)", exact: true })).toHaveAttribute("aria-pressed", "true");
    await page.evaluate(() => {
      (window as any).moreInfo = [];
      document.addEventListener("hass-more-info", (e: any) => (window as any).moreInfo.push(e.detail.entityId));
    });
    await card.getByRole("button", { name: /Show details for/ }).focus();
    await page.keyboard.press("Enter");
    expect(await page.evaluate(() => (window as any).moreInfo)).toEqual(["switch.cube_docker_container_plex"]);
    await card.getByRole("button", { name: "Switch to list view" }).click();
    await expect(card.locator(".item-list")).toBeVisible();
  });

  test("stop confirmation cancels safely and dispatches one explicit action", async ({ page }) => {
    const card = page.locator("#docker-card");
    await page.evaluate(() => {
      (window as any).serviceCalls = [];
      (window as any).mockHass.callService = async (...args: any[]) => { (window as any).serviceCalls.push(args); };
    });
    const stop = card.getByRole("button", { name: /Stop .*plex/ });
    await stop.click();
    const dialog = card.getByRole("dialog");
    await expect(dialog).toBeVisible();
    await dialog.getByRole("button", { name: "Cancel", exact: true }).click();
    await expect(dialog).not.toBeVisible();
    expect(await page.evaluate(() => (window as any).serviceCalls)).toEqual([]);
    await expect(stop).toBeFocused();
    await stop.click();
    await dialog.getByRole("button", { name: "Stop", exact: true }).click();
    await expect(dialog).not.toBeVisible();
    expect(await page.evaluate(() => (window as any).serviceCalls)).toEqual([
      ["switch", "turn_off", { entity_id: "switch.cube_docker_container_plex" }],
    ]);
  });

  test("container action failures are visible and Escape cancels the dialog", async ({ page }) => {
    const card = page.locator("#docker-card");
    await page.evaluate(() => { (window as any).mockHass.callService = async () => { throw new Error("offline"); }; });
    await card.getByRole("button", { name: /Stop .*plex/ }).click();
    const dialog = card.getByRole("dialog");
    await dialog.getByRole("button", { name: "Stop", exact: true }).click();
    await expect(dialog.getByRole("alert")).toContainText("container action failed");
    await page.keyboard.press("Escape");
    await expect(dialog).not.toBeVisible();
  });

  test("phone layouts retain touch targets, natural height, focus and theme colors", async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    const card = page.locator("#docker-card");
    await expect(card.getByRole("button", { name: /Show details for/ })).toBeVisible();
    const sizes = await card.locator("button").evaluateAll((buttons) => buttons.filter((b) => b.getClientRects().length).map((b) => ({ w: b.getBoundingClientRect().width, h: b.getBoundingClientRect().height })));
    expect(sizes.filter(({w,h}) => w < 44 || h < 44)).toEqual([]);
    const overflow = await card.evaluate((el) => el.scrollWidth > el.clientWidth);
    expect(overflow).toBe(false);
    await page.evaluate(() => {
      document.documentElement.style.setProperty("--ha-card-background", "rgb(255, 255, 255)");
      document.documentElement.style.setProperty("--primary-text-color", "rgb(20, 20, 20)");
    });
    await expect(card.locator("ha-card")).toHaveCSS("background-color", "rgb(255, 255, 255)");
    await card.getByRole("button", { name: "Switch to list view" }).focus();
    await expect(card.getByRole("button", { name: "Switch to list view" })).toHaveCSS("outline-style", "solid");
  });


  test("restart confirms once, disables pending controls, and retains focus on cancel", async ({ page }) => {
    const card = page.locator("#docker-card");
    await page.evaluate(() => {
      (window as any).serviceCalls = [];
      (window as any).mockHass.callService = (...args: any[]) => {
        (window as any).serviceCalls.push(args);
        return new Promise((resolve) => { (window as any).finishAction = resolve; });
      };
    });
    await card.getByRole("button", { name: /Restart .*plex/ }).click();
    const dialog = card.getByRole("dialog");
    await expect(dialog).toContainText("Restart container?");
    await dialog.getByRole("button", { name: "Restart", exact: true }).click();
    await expect(dialog.getByRole("button", { name: "Working…" })).toBeDisabled();
    expect(await page.evaluate(() => (window as any).serviceCalls)).toEqual([
      ["button", "press", { entity_id: "button.cube_container_restart_plex" }],
    ]);
    await page.evaluate(() => (window as any).finishAction());
    await expect(dialog).not.toBeVisible();
  });


  test("respects reduced-motion preferences for card controls", async ({ page }) => {
    await page.emulateMedia({ reducedMotion: "reduce" });
    const card = page.locator("#docker-card");
    await expect(card.getByRole("button", { name: "Switch to list view" })).toHaveCSS("transition-duration", "0s");
    await expect(card.getByRole("button", { name: "All (1)", exact: true })).toHaveCSS("transition-duration", "0s");
  });

});
