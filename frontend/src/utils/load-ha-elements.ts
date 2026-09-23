/**
 * Load Home Assistant built-in elements (ha-card, ha-icon, etc.) so they can
 * be used inside our custom panel.
 *
 * This uses the well-known community technique of loading HA's own panel
 * resolver to trigger element registration.
 */

const LOAD_TIMEOUT_MS = 10000;

interface PartialPanelResolver extends HTMLElement {
  hass: { panels: { url_path: string; component_name: string }[] };
  routerOptions: { routes: Record<string, { load: () => Promise<unknown> }> };
  _updateRoutes: () => void;
}

async function loadHaElementsImpl(): Promise<void> {
  await customElements.whenDefined("partial-panel-resolver");

  const ppr = document.createElement("partial-panel-resolver") as PartialPanelResolver;
  ppr.hass = {
    panels: [
      {
        url_path: "tmp",
        component_name: "config",
      },
    ],
  };
  ppr._updateRoutes();
  await ppr.routerOptions.routes.tmp.load();

  if (!customElements.get("ha-card")) {
    await customElements.whenDefined("ha-card");
  }
}

export const loadHaElements = async (): Promise<void> => {
  if (customElements.get("ha-card")) return;

  try {
    await Promise.race([
      loadHaElementsImpl(),
      new Promise<void>((_, reject) =>
        setTimeout(
          () =>
            reject(new Error(`Timeout waiting for HA elements (${LOAD_TIMEOUT_MS}ms)`)),
          LOAD_TIMEOUT_MS,
        ),
      ),
    ]);
  } catch (err) {
    console.warn("[kubernetes-panel] Failed to load HA elements:", err);
  }
};
