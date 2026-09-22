/** Pure helpers shared by the panel views. */

/** Human-readable node condition names, keyed by the API's snake_case flags. */
export const CONDITION_LABELS: Record<string, string> = {
  memory_pressure: "Memory Pressure",
  disk_pressure: "Disk Pressure",
  pid_pressure: "PID Pressure",
  network_unavailable: "Network Unavailable",
};

/** Age of an ISO timestamp as a compact "5s" / "5m" / "2h" / "3d" string. */
export function formatAge(iso: string | null | undefined): string {
  if (!iso || iso === "N/A") return "N/A";
  const created = new Date(iso).getTime();
  const now = Date.now();
  const diff = Math.max(0, Math.floor((now - created) / 1000));
  if (diff < 60) return `${diff}s`;
  if (diff < 3600) return `${Math.floor(diff / 60)}m`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h`;
  return `${Math.floor(diff / 86400)}d`;
}

/** Time since a unix timestamp (seconds) as "5m ago"; "Never" for 0. */
export function formatRelative(epochSeconds: number): string {
  if (!epochSeconds) return "Never";
  const now = Date.now() / 1000;
  const diff = Math.max(0, Math.floor(now - epochSeconds));
  if (diff < 60) return `${diff}s ago`;
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
  return `${Math.floor(diff / 86400)}d ago`;
}

/** Copy `set` with `key` added if absent, removed if present (Lit needs a new ref). */
export function toggleInSet<T>(set: Set<T>, key: T): Set<T> {
  const updated = new Set(set);
  if (updated.has(key)) {
    updated.delete(key);
  } else {
    updated.add(key);
  }
  return updated;
}

/**
 * Message of a caught value. HA's `callWS` rejects with a plain
 * `{ code, message }` object rather than an `Error`, so any object with a
 * non-empty string `message` counts.
 */
export function errorMessage(err: unknown, fallback: string): string {
  if (
    typeof err === "object" &&
    err !== null &&
    "message" in err &&
    typeof err.message === "string" &&
    err.message
  ) {
    return err.message;
  }
  return fallback;
}
