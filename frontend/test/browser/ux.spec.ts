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
}

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
