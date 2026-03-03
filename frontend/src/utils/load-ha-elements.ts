/**
 * Load Home Assistant built-in elements (ha-card, ha-icon, etc.) so they can
 * be used inside our custom panel.
 *
 * This uses the well-known community technique of loading HA's own panel
 * resolver to trigger element registration.
 */
export const loadHaElements = async (): Promise<void> => {
  if (customElements.get("ha-card")) return;

  await customElements.whenDefined("partial-panel-resolver");

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
    await customElements.whenDefined("ha-card");
  }
};
