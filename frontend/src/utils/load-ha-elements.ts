/**
 * Load Home Assistant built-in elements (ha-card, ha-icon, etc.) so they can
 * be used inside our custom panel.
 *
 * This uses the well-known community technique of loading HA's own panel
 * resolver to trigger element registration.
 */

const LOAD_TIMEOUT_MS = 10000;

function withTimeout<T>(promise: Promise<T>, ms: number, label: string): Promise<T> {
  return Promise.race([
    promise,
    new Promise<T>((_, reject) =>
      setTimeout(() => reject(new Error(`Timeout waiting for ${label} (${ms}ms)`)), ms),
    ),
  ]);
}

export const loadHaElements = async (): Promise<void> => {
  if (customElements.get("ha-card")) return;

  try {
    await withTimeout(
      customElements.whenDefined("partial-panel-resolver"),
      LOAD_TIMEOUT_MS,
      "partial-panel-resolver",
    );

    const ppr = document.createElement("partial-panel-resolver") as any;
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
      await withTimeout(
        customElements.whenDefined("ha-card"),
        LOAD_TIMEOUT_MS,
        "ha-card",
      );
    }
  } catch (err) {
    console.warn("[kubernetes-panel] Failed to load HA elements:", err);
  }
};
