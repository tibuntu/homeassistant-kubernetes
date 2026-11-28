/**
 * URL navigation shared by the panel and its views.
 *
 * Mirrors Home Assistant's own `navigate()` (src/common/navigate.ts): push a
 * history entry, then fire `location-changed` on `window` with
 * `detail.replace` so HA's router updates the panel's `route`.
 */
export function navigate(url: string): void {
  history.pushState(null, "", url);
  window.dispatchEvent(
    new CustomEvent("location-changed", { detail: { replace: false } }),
  );
}

/** One query parameter of the current URL (`null` when absent). */
export function queryParam(name: string): string | null {
  return new URLSearchParams(location.search).get(name);
}

/** `value` when it is one of `allowed`, else `fallback` (typos, stale values). */
export function oneOf<T extends string>(
  value: string | null,
  allowed: readonly T[],
  fallback: T,
): T {
  return allowed.includes(value as T) ? (value as T) : fallback;
}

/**
 * Write filter state into the query string with a history *replace* (no new
 * entry per keystroke) and without a `location-changed` event, so HA's router
 * does not churn. Empty values drop the parameter; other parameters stay.
 */
export function replaceQuery(params: Record<string, string>): void {
  const query = new URLSearchParams(location.search);
  for (const [key, value] of Object.entries(params)) {
    if (value) query.set(key, value);
    else query.delete(key);
  }
  const qs = query.toString();
  history.replaceState(history.state, "", `${location.pathname}${qs ? `?${qs}` : ""}`);
}
