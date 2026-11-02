/**
 * Minimal HomeAssistant interface covering the subset of the HA frontend
 * API surface used by this panel.  The canonical definition lives in the
 * home-assistant-frontend repo but is not published as a standalone npm
 * package, so we maintain a slim local copy instead.
 */
export interface HomeAssistant {
  user?: { id: string; name: string; is_admin: boolean };
  callWS: <T>(msg: Record<string, unknown>) => Promise<T>;
  callService: (
    domain: string,
    service: string,
    data?: Record<string, unknown>,
    target?: Record<string, unknown>,
    notifyOnError?: boolean,
    returnResponse?: boolean,
  ) => Promise<ServiceCallResponse>;
  connection: {
    subscribeMessage: <T>(
      callback: (msg: T) => void,
      subscribeMessage: { type: string } & Record<string, unknown>,
    ) => Promise<() => Promise<void>>;
  };
}

/** What `callService` resolves to; `response` is set with `returnResponse`. */
export interface ServiceCallResponse {
  response?: unknown;
}
