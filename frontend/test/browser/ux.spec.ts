import { expect, test, type Page } from "@playwright/test";

const CARDS = [
  "server-card",
  "storage-card",
  "shares-card",
  "docker-card",
  "ups-card",
  "vm-card",
  "network-card",
  "zfs-card",
  "fans-card",
  "gpu-card",
  "notifications-card",
  "maintenance-card",
  "remote-shares-card",
  "unassigned-devices-card",
  "dashboard-card",
];

test.beforeEach(async ({ page }) => {
  await page.goto("/test/browser/fixture.html");
  await page.waitForFunction(
    () => (window as unknown as { fixtureReady?: boolean }).fixtureReady === true
  );
});

async function setWidth(page: Page, width: number, dir = "ltr"): Promise<void> {
  await page.evaluate(
    ([w, d]) => {
      const container = document.getElementById("container")!;
      container.style.width = `${w}px`;
      container.style.maxWidth = `${w}px`;
      container.dir = String(d);
    },
    [width, dir]
  );
}

/** Return what spills out of each card: the card itself and its elements. */
async function overflowing(page: Page): Promise<string[]> {
  return page.evaluate((cards) => {
    const found: string[] = [];
    for (const id of cards) {
      const host = document.getElementById(id)!;
      const box = host.getBoundingClientRect();
      const walk = (root: ShadowRoot): void => {
        for (const el of root.querySelectorAll<HTMLElement>("*")) {
          if (el.closest(".tab-strip")) continue;
          const r = el.getBoundingClientRect();
          if (r.width > 0 && (r.right > box.right + 1 || r.left < box.left - 1)) {
            found.push(`${id}: ${el.tagName.toLowerCase()}.${el.className}`);
          }
          if (el.shadowRoot) walk(el.shadowRoot);
        }
      };
      walk(host.shadowRoot!);
    }
    return found;
  }, CARDS);
}

test("row content does not overlap at 300px", async ({ page }) => {
  await setWidth(page, 300, "ltr");
  const squeezed = await page.evaluate((cards) => {
    const found: string[] = [];
    for (const id of cards) {
      for (const el of document.getElementById(id)!.shadowRoot!.querySelectorAll<HTMLElement>(".row-left")) {
        if (el.clientWidth > 0 && el.scrollWidth > el.clientWidth + 1) found.push(id);
      }
    }
    return found;
  }, CARDS);
  expect(squeezed).toEqual([]);
});

for (const dir of ["ltr", "rtl"]) {
  test(`every card fits a 300px ${dir} column`, async ({ page }) => {
    await setWidth(page, 300, dir);
    expect(await overflowing(page)).toEqual([]);
  });

  for (const embedded of [false, true]) {
    test(`long names fit all 15 cards at 300px ${dir}, embedded=${embedded}`, async ({ page }) => {
      await page.setViewportSize({ width: 1440, height: 1000 });
      await page.goto(`/test/browser/fixture.html?width=300&dir=${dir}&longNames=1${embedded ? "&embedded=1" : ""}`);
      await page.waitForFunction(() => (window as unknown as { fixtureReady?: boolean }).fixtureReady);
      expect(await overflowing(page)).toEqual([]);
      const overflow = await page.evaluate((cards) => cards.filter((id) => {
        const host = document.getElementById(id)!;
        return host.scrollWidth > host.clientWidth;
      }), CARDS);
      expect(overflow).toEqual([]);

      const vmName = page.locator("#vm-card .entity-name").first();
      const gpuName = page.locator("#gpu-card .entity-name").first();
      for (const name of [vmName, gpuName]) {
        await expect(name).toHaveCSS("text-overflow", "ellipsis");
        expect(await name.evaluate((el) => el.scrollWidth > el.clientWidth)).toBe(true);
      }
      expect(await page.locator("#ups-card .ups-rings").evaluate((el) => getComputedStyle(el).gridTemplateColumns.split(" ").length)).toBe(1);
      const driver = page.locator("#gpu-card .gpu-driver");
      await expect(driver).toHaveCSS("white-space", "normal");
      expect(await driver.evaluate((el) => el.getBoundingClientRect().height)).toBeGreaterThan(30);

      const technical = page.locator("#network-card .ltr-value");
      expect(await technical.count()).toBeGreaterThan(0);
      for (const value of await technical.all()) {
        await expect(value).toHaveCSS("direction", "ltr");
        await expect(value).toHaveCSS("unicode-bidi", "isolate");
      }
    });
  }
}

test("named containers live inside cards and reflow UPS at 320px", async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 1000 });
  const host = page.locator("#ups-card");
  await expect(host).toHaveCSS("container-type", "normal");
  const content = host.locator(".uma-card-content");
  await expect(content).toHaveCSS("container-name", "unraid-card");
  await content.evaluate((el) => { (el as HTMLElement).style.width = "321px"; });
  const columns = () => host.locator(".ups-rings").evaluate((el) => getComputedStyle(el).gridTemplateColumns.split(" ").length);
  expect(await columns()).toBe(2);
  await content.evaluate((el) => { (el as HTMLElement).style.width = "320px"; });
  expect(await columns()).toBe(1);
});

test("converted row buttons activate once on Space release", async ({ page }) => {
  for (const id of ["shares-card", "maintenance-card", "ups-card", "network-card", "zfs-card", "unassigned-devices-card", "fans-card"]) {
    const card = page.locator(`#${id}`);
    await card.evaluate((el) => {
      (window as unknown as { opened: string[] }).opened = [];
      el.addEventListener("hass-more-info", (event) => {
        (window as unknown as { opened: string[] }).opened.push((event as CustomEvent<{ entityId: string }>).detail.entityId);
      });
    });
    const button = card.locator("button.interactive:not(:disabled)").first();
    await button.focus();
    await page.keyboard.down("Space");
    expect(await page.evaluate(() => (window as unknown as { opened: string[] }).opened)).toEqual([]);
    await page.keyboard.up("Space");
    const opened = await page.evaluate(() => (window as unknown as { opened: string[] }).opened);
    expect(opened).toHaveLength(1);
    expect(opened[0]).toMatch(/^(sensor|binary_sensor)\./);
  }
});

test("clickable rows and gauges are native buttons", async ({ page }) => {
  const bad = await page.evaluate((cards) => {
    const found: string[] = [];
    for (const id of cards) {
      const root = document.getElementById(id)!.shadowRoot!;
      for (const el of root.querySelectorAll('[role="button"], [tabindex="0"]:not(button)')) {
        found.push(`${id}: ${el.tagName} ${el.className}`);
      }
    }
    return found;
  }, CARDS);
  expect(bad).toEqual([]);
});

test("HA font and spacing tokens reach the cards", async ({ page }) => {
  const size = await page.evaluate(() => {
    document.documentElement.style.setProperty("--ha-font-size-l", "31px");
    const root = document.getElementById("server-card")!.shadowRoot!;
    return getComputedStyle(root.querySelector(".header-title")!).fontSize;
  });
  expect(size).toBe("31px");
});

test("buttons have Home Assistant sized touch targets", async ({ page }) => {
  const small = await page.evaluate((cards) => {
    const found: string[] = [];
    for (const id of cards) {
      const root = document.getElementById(id)!.shadowRoot!;
      for (const el of root.querySelectorAll<HTMLButtonElement>("button:not(:disabled)")) {
        const r = el.getBoundingClientRect();
        const min = el.classList.contains("btn-icon") ? 48 : 40;
        if (r.height > 0 && (r.height < min || r.width < min)) {
          found.push(`${id}: ${el.className} ${r.width}x${r.height}`);
        }
      }
    }
    return found;
  }, CARDS);
  expect(small).toEqual([]);
});

test("gauges and rows open details by keyboard, and without an entity are disabled", async ({
  page,
}) => {
  const ring = page.locator("#server-card").locator("button.ring-card").first();
  await ring.focus();
  await expect(ring).toBeFocused();
  await page.evaluate(() => {
    document.getElementById("server-card")!.addEventListener("hass-more-info", (event) => {
      (window as unknown as { opened?: string }).opened = (
        event as CustomEvent<{ entityId: string }>
      ).detail.entityId;
    });
  });
  await page.keyboard.press("Enter");
  await expect
    .poll(() => page.evaluate(() => (window as unknown as { opened?: string }).opened))
    .toContain("sensor.");

  const disabled = await page.evaluate(() => {
    const el = document.getElementById("server-card")! as HTMLElement & {
      hass: { states: Record<string, unknown> };
    };
    el.hass = { ...el.hass, states: {} };
    return (el as unknown as { updateComplete: Promise<boolean> }).updateComplete.then(
      () =>
        Array.from(el.shadowRoot!.querySelectorAll<HTMLButtonElement>("button.ring-card")).every(
          (button) => button.disabled
        )
    );
  });
  expect(disabled).toBe(true);
});

test("focus is visible on a control", async ({ page }) => {
  const ring = page.locator("#server-card").locator("button.ring-card").first();
  await page.keyboard.press("Tab");
  await ring.focus();
  await page.keyboard.press("Shift+Tab");
  await page.keyboard.press("Tab");
  const outline = await page.evaluate(() => {
    const active = document.activeElement?.shadowRoot?.activeElement;
    return active ? getComputedStyle(active).outlineStyle : "";
  });
  expect(outline).toBe("solid");
});

test("dashboard tabs support selected states and arrow, Home and End keys", async ({ page }) => {
  const card = page.locator("#dashboard-card");
  const tab = (name: string) => card.getByRole("tab", { name, exact: true });
  await expect(tab("Overview")).toHaveAttribute("aria-selected", "true");
  await expect(card.getByRole("tabpanel")).toBeVisible();

  await tab("Overview").focus();
  await page.keyboard.press("ArrowRight");
  await expect(tab("Storage")).toBeFocused();
  await expect(tab("Storage")).toHaveAttribute("aria-selected", "true");
  await expect(tab("Overview")).toHaveAttribute("tabindex", "-1");

  await page.keyboard.press("End");
  await expect(tab("Notifications")).toBeFocused();
  await page.keyboard.press("ArrowRight");
  await expect(tab("Overview")).toBeFocused();
  await page.keyboard.press("ArrowLeft");
  await expect(tab("Notifications")).toBeFocused();
  await page.keyboard.press("Home");
  await expect(tab("Overview")).toBeFocused();
});

test("reduced motion removes card transitions", async ({ page }) => {
  await page.emulateMedia({ reducedMotion: "reduce" });
  const duration = await page.evaluate(() => {
    const root = document.getElementById("server-card")!.shadowRoot!;
    const el = root.querySelector(".progress-fill, .tab-btn, .disk-row, .list-row, .btn");
    return el ? getComputedStyle(el).transitionDuration : "0s";
  });
  expect(duration).toBe("0s");
});

for (const { theme, text, background } of [
  { theme: "light", text: "rgb(33, 33, 33)", background: "rgb(255, 255, 255)" },
  { theme: "dark", text: "rgb(225, 225, 225)", background: "rgb(28, 28, 28)" },
]) {
  test(`${theme} theme colours reach the card`, async ({ page }) => {
    const colours = await page.evaluate(
      ({ t, b }) => {
        const root = document.documentElement.style;
        root.setProperty("--primary-text-color", t);
        root.setProperty("--card-background-color", b);
        root.setProperty("--ha-card-background", b);
        const card = document.getElementById("server-card")!.shadowRoot!.querySelector("ha-card")!;
        const style = getComputedStyle(card);
        return [style.color, style.backgroundColor];
      },
      { t: text, b: background }
    );
    expect(colours).toEqual([text, background]);
  });
}
