/**
 * Mounts the real panel against a fake `hass` so Playwright can drive it
 * without Home Assistant. Responses come from `fixtures.ts`; every WebSocket
 * message and service call is recorded on `window.__k8s` for assertions.
 *
 * Query string: `?fail=<ws type>` (repeatable) makes those WebSocket calls
 * reject until the spec clears `window.__k8s.fail`. `?admin=0` mounts the
 * panel as a non-admin user.
 */
import { KubernetesPanel } from "../src/kubernetes-panel";
import type { HomeAssistant } from "../src/types/homeassistant";
import { RESPONSES } from "./fixtures";

interface ServiceCall {
  domain: string;
  service: string;
  data?: Record<string, unknown>;
}

declare global {
  interface Window {
    __k8s: {
      /** Every `callWS` message, in order. */
      calls: Record<string, unknown>[];
      /** Every `callService` call, in order. */
      services: ServiceCall[];
      /** WebSocket types that reject. */
      fail: Set<string>;
      /** Fire a `kubernetes/subscribe_updates` push to every subscriber. */
      push: () => void;
    };
  }
}

const calls: Record<string, unknown>[] = [];
const services: ServiceCall[] = [];
const fail = new Set(new URLSearchParams(location.search).getAll("fail"));
const subscribers: (() => void)[] = [];
window.__k8s = { calls, services, fail, push: () => subscribers.forEach((cb) => cb()) };

// Stand-ins for HA's own elements: an undefined custom element would render
// its children anyway, but defining `ha-card` makes `loadHaElements()` return
// early instead of waiting ten seconds for HA's panel resolver.
for (const tag of ["ha-card", "ha-icon", "ha-circular-progress"]) {
  customElements.define(tag, class extends HTMLElement {});
}

const hass: HomeAssistant = {
  user: {
    id: "harness",
    name: "Harness",
    is_admin: new URLSearchParams(location.search).get("admin") !== "0",
  },
  async callWS<T>(msg: Record<string, unknown>): Promise<T> {
    calls.push(msg);
    const type = String(msg.type);
    if (fail.has(type)) throw new Error(`harness: ${type} failed`);
    if (!(type in RESPONSES)) throw new Error(`harness: no fixture for ${type}`);
    return structuredClone(RESPONSES[type]) as T;
  },
  async callService(domain, service, data) {
    services.push({ domain, service, data });
  },
  connection: {
    async subscribeMessage<T>(callback: (msg: T) => void, msg: { type: string }) {
      if (msg.type === "kubernetes/subscribe_updates") {
        subscribers.push(() => callback({} as T));
      }
      return async () => {};
    },
  },
};

const panel = new KubernetesPanel();
panel.hass = hass;
document.body.append(panel);
