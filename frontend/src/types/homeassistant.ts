/**
 * Minimal HomeAssistant interface covering the subset of the HA frontend
 * API surface used by this panel.  The canonical definition lives in the
 * home-assistant-frontend repo but is not published as a standalone npm
 * package, so we maintain a slim local copy instead.
 */
export interface HomeAssistant {
  callWS: <T>(msg: Record<string, unknown>) => Promise<T>;
  callService: (
    domain: string,
    service: string,
    data?: Record<string, unknown>,
  ) => Promise<void>;
}
