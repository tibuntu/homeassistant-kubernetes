import { LitElement, html, nothing, PropertyValues, TemplateResult } from "lit";
import { property, state } from "lit/decorators.js";
import type { HomeAssistant } from "../types/homeassistant";
import { errorMessage } from "../utils/format";

/**
 * Base class for the panel's data views.
 *
 * Owns the load/refresh lifecycle every view shares: initial load, 60 s
 * polling (paused while the tab is hidden), the `kubernetes/subscribe_updates`
 * push subscription with a 1 s debounce, an in-flight guard, and the
 * loading / error / empty preamble. Subclasses implement `fetchData()` (call
 * the WebSocket API and assign `this._data`) and start `render()` with
 * `renderState()`.
 *
 * `T` is the WebSocket response type stored in `_data`.
 */
export abstract class K8sDataView<T> extends LitElement {
  @property({ attribute: false }) public hass!: HomeAssistant;

  @state() protected _data: T | null = null;
  @state() protected _loading = true;
  @state() protected _error: string | null = null;

  /** Poll interval in ms; `0` disables polling and the visibility handling. */
  protected pollMs = 60_000;
  /** Subscribe to coordinator push updates. */
  protected subscribe = true;
  /** Error shown when `fetchData()` throws something without a message. */
  protected loadErrorFallback = "Failed to load data";
  /** Text of the empty state. */
  protected emptyMessage = "No Kubernetes clusters configured.";

  private _refreshInterval?: ReturnType<typeof setInterval>;
  private _loadingInFlight = false;
  private _boundVisibilityHandler = this._handleVisibilityChange.bind(this);
  private _unsubUpdates?: () => Promise<void>;
  private _updateDebounce?: ReturnType<typeof setTimeout>;
  private _reloadTimer?: ReturnType<typeof setTimeout>;

  /** Fetch from the backend and assign `this._data`. Throw to show the error card. */
  protected abstract fetchData(): Promise<void>;

  /**
   * Whether a previous load produced data. While `false`, `_loadData()` shows
   * the spinner; afterwards refreshes keep the stale view visible.
   */
  protected hasData(): boolean {
    return this._data !== null;
  }

  protected firstUpdated(_changedProps: PropertyValues): void {
    this._loadData();
    if (this.pollMs > 0) {
      this._startPolling();
      document.addEventListener("visibilitychange", this._boundVisibilityHandler);
    }
    if (this.subscribe) void this._subscribeUpdates();
  }

  disconnectedCallback(): void {
    super.disconnectedCallback();
    this._stopPolling();
    document.removeEventListener("visibilitychange", this._boundVisibilityHandler);
    void this._unsubUpdates?.().catch(() => {});
    this._unsubUpdates = undefined;
    if (this._updateDebounce) {
      clearTimeout(this._updateDebounce);
      this._updateDebounce = undefined;
    }
    if (this._reloadTimer) {
      clearTimeout(this._reloadTimer);
      this._reloadTimer = undefined;
    }
  }

  private _handleVisibilityChange(): void {
    if (document.hidden) {
      this._stopPolling();
    } else {
      this._loadData();
      this._startPolling();
    }
  }

  private _startPolling(): void {
    if (!this._refreshInterval) {
      this._refreshInterval = setInterval(() => this._loadData(), this.pollMs);
    }
  }

  private _stopPolling(): void {
    if (this._refreshInterval) {
      clearInterval(this._refreshInterval);
      this._refreshInterval = undefined;
    }
  }

  private async _subscribeUpdates(): Promise<void> {
    try {
      const unsub = await this.hass.connection.subscribeMessage(
        () => this._scheduleLoad(),
        { type: "kubernetes/subscribe_updates" },
      );
      if (!this.isConnected) {
        void unsub().catch(() => {});
        return;
      }
      this._unsubUpdates = unsub;
    } catch {
      // Backend without subscription support — interval polling covers it.
    }
  }

  private _scheduleLoad(): void {
    if (document.hidden) return;
    if (this._updateDebounce) return;
    this._updateDebounce = setTimeout(() => {
      this._updateDebounce = undefined;
      this._loadData();
    }, 1000);
  }

  /** Reload after `delayMs`, replacing any pending reload. */
  protected _scheduleReload(delayMs: number): void {
    if (this._reloadTimer) clearTimeout(this._reloadTimer);
    this._reloadTimer = setTimeout(() => {
      this._reloadTimer = undefined;
      this._loadData();
    }, delayMs);
  }

  /** Guarded load: one request at a time, spinner only before the first data. */
  protected async _loadData(): Promise<void> {
    if (this._loadingInFlight) return;
    this._loadingInFlight = true;
    if (!this.hasData()) {
      this._loading = true;
    }
    this._error = null;
    try {
      await this.fetchData();
    } catch (err: unknown) {
      this._error = errorMessage(err, this.loadErrorFallback);
    } finally {
      this._loading = false;
      this._loadingInFlight = false;
    }
  }

  /**
   * Loading spinner, error card or empty message, or `nothing` when the view
   * should render its data. `empty` is the view's own "no items" test.
   */
  protected renderState(empty: boolean): TemplateResult | typeof nothing {
    if (this._loading) {
      return html`
        <div class="loading">
          <ha-circular-progress indeterminate></ha-circular-progress>
        </div>
      `;
    }

    if (this._error) {
      return html`
        <ha-card>
          <div class="error-card">
            <ha-icon icon="mdi:alert-circle"></ha-icon>
            <p>${this._error}</p>
            <button class="retry-btn" @click=${this._loadData}>Retry</button>
          </div>
        </ha-card>
      `;
    }

    if (empty) {
      return html`<div class="empty">${this.emptyMessage}</div>`;
    }

    return nothing;
  }
}
