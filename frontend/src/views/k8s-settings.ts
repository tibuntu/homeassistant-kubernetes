import { LitElement, html, css, nothing, PropertyValues } from "lit";
import { customElement, property, state } from "lit/decorators.js";

interface ConfigEntry {
  entry_id: string;
  cluster_name: string;
  host: string;
  port: number;
  verify_ssl: boolean;
  monitor_all_namespaces: boolean;
  namespaces: string[];
  device_grouping_mode: string;
  switch_update_interval: number;
  scale_verification_timeout: number;
  scale_cooldown: number;
  panel_enabled: boolean;
  watch_enabled: boolean;
  healthy: boolean | null;
}

interface ConfigResponse {
  entries: ConfigEntry[];
}

@customElement("k8s-settings")
export class K8sSettings extends LitElement {
  @property({ attribute: false }) public hass!: any;

  @state() private _data: ConfigResponse | null = null;
  @state() private _loading = true;
  @state() private _error: string | null = null;

  protected firstUpdated(_changedProps: PropertyValues): void {
    this._loadData();
  }

  private async _loadData(): Promise<void> {
    this._loading = true;
    this._error = null;
    try {
      const result: ConfigResponse = await this.hass.callWS({
        type: "kubernetes/config/list",
      });
      this._data = result;
    } catch (err: any) {
      this._error = err.message || "Failed to load configuration";
    } finally {
      this._loading = false;
    }
  }

  private _navigateToIntegration(): void {
    window.open("/config/integrations/integration/kubernetes", "_blank");
  }

  static styles = css`
    :host {
      display: block;
    }

    .loading {
      display: flex;
      justify-content: center;
      padding: 64px 0;
    }

    .error-card {
      display: flex;
      flex-direction: column;
      align-items: center;
      padding: 32px;
      text-align: center;
      color: var(--error-color, #db4437);
      --mdc-icon-size: 48px;
    }

    .error-card p {
      margin: 16px 0;
    }

    .retry-btn {
      cursor: pointer;
      padding: 8px 24px;
      border: 1px solid var(--primary-color);
      border-radius: 4px;
      background: transparent;
      color: var(--primary-color);
      font-size: 14px;
    }

    .retry-btn:hover {
      background: var(--primary-color);
      color: var(--text-primary-color, #fff);
    }

    .empty {
      text-align: center;
      padding: 64px 16px;
      color: var(--secondary-text-color);
      font-size: 16px;
    }

    .entry-section {
      margin-bottom: 24px;
    }

    .entry-header {
      display: flex;
      align-items: center;
      gap: 12px;
      margin-bottom: 16px;
      flex-wrap: wrap;
    }

    .entry-name {
      font-size: 24px;
      font-weight: 500;
      color: var(--primary-text-color);
    }

    .badge {
      display: inline-flex;
      align-items: center;
      gap: 4px;
      padding: 2px 10px;
      border-radius: 12px;
      font-size: 12px;
      font-weight: 500;
    }

    .badge-healthy {
      background: rgba(76, 175, 80, 0.15);
      color: #4caf50;
    }

    .badge-unhealthy {
      background: rgba(244, 67, 54, 0.15);
      color: #f44336;
    }

    .badge-unknown {
      background: rgba(158, 158, 158, 0.15);
      color: #9e9e9e;
    }

    .cards-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(360px, 1fr));
      gap: 16px;
      margin-bottom: 16px;
    }

    .settings-card {
      padding: 20px;
      border-radius: 12px;
    }

    .card-title {
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 16px;
      font-weight: 500;
      color: var(--primary-text-color);
      margin-bottom: 16px;
      --mdc-icon-size: 20px;
    }

    .card-title ha-icon {
      color: var(--primary-color);
    }

    .setting-row {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 8px 0;
      border-bottom: 1px solid var(--divider-color);
      font-size: 14px;
    }

    .setting-row:last-child {
      border-bottom: none;
    }

    .setting-label {
      color: var(--secondary-text-color);
    }

    .setting-value {
      color: var(--primary-text-color);
      font-weight: 500;
      text-align: right;
      max-width: 60%;
      word-break: break-all;
    }

    .setting-value-bool {
      display: inline-flex;
      align-items: center;
      gap: 4px;
      --mdc-icon-size: 16px;
    }

    .bool-true {
      color: #4caf50;
    }

    .bool-false {
      color: var(--secondary-text-color);
    }

    .namespace-tags {
      display: flex;
      flex-wrap: wrap;
      gap: 4px;
      justify-content: flex-end;
    }

    .ns-tag {
      padding: 2px 8px;
      border-radius: 4px;
      background: rgba(var(--rgb-primary-color, 3, 169, 244), 0.1);
      color: var(--primary-color);
      font-size: 12px;
    }

    .actions-bar {
      display: flex;
      gap: 12px;
      margin-top: 16px;
      flex-wrap: wrap;
    }

    .action-btn {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      cursor: pointer;
      padding: 8px 20px;
      border: 1px solid var(--divider-color);
      border-radius: 8px;
      background: transparent;
      color: var(--primary-text-color);
      font-size: 14px;
      transition:
        background 0.2s,
        border-color 0.2s;
      --mdc-icon-size: 18px;
    }

    .action-btn:hover {
      background: rgba(var(--rgb-primary-color, 3, 169, 244), 0.08);
      border-color: var(--primary-color);
      color: var(--primary-color);
    }
  `;

  protected render() {
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

    if (!this._data?.entries.length) {
      return html`<div class="empty">No Kubernetes entries configured.</div>`;
    }

    return html`${this._data.entries.map((e) => this._renderEntry(e))}`;
  }

  private _renderEntry(entry: ConfigEntry) {
    return html`
      <div class="entry-section">
        <div class="entry-header">
          <span class="entry-name">${entry.cluster_name}</span>
          ${this._renderHealthBadge(entry.healthy)}
        </div>

        <div class="cards-grid">
          ${this._renderConnectionCard(entry)} ${this._renderNamespaceCard(entry)}
          ${this._renderTimingCard(entry)} ${this._renderFeaturesCard(entry)}
        </div>

        <div class="actions-bar">
          <button class="action-btn" @click=${this._navigateToIntegration}>
            <ha-icon icon="mdi:cog"></ha-icon>
            Configure Integration
          </button>
        </div>
      </div>
    `;
  }

  private _renderHealthBadge(healthy: boolean | null) {
    if (healthy === true) {
      return html`<span class="badge badge-healthy">Connected</span>`;
    }
    if (healthy === false) {
      return html`<span class="badge badge-unhealthy">Disconnected</span>`;
    }
    return html`<span class="badge badge-unknown">Unknown</span>`;
  }

  private _renderConnectionCard(entry: ConfigEntry) {
    return html`
      <ha-card class="settings-card">
        <div class="card-title">
          <ha-icon icon="mdi:connection"></ha-icon>
          Connection
        </div>
        <div class="setting-row">
          <span class="setting-label">Host</span>
          <span class="setting-value">${entry.host}</span>
        </div>
        <div class="setting-row">
          <span class="setting-label">Port</span>
          <span class="setting-value">${entry.port}</span>
        </div>
        <div class="setting-row">
          <span class="setting-label">Verify SSL</span>
          <span class="setting-value">${this._renderBool(entry.verify_ssl)}</span>
        </div>
      </ha-card>
    `;
  }

  private _renderNamespaceCard(entry: ConfigEntry) {
    return html`
      <ha-card class="settings-card">
        <div class="card-title">
          <ha-icon icon="mdi:folder-multiple"></ha-icon>
          Namespaces
        </div>
        <div class="setting-row">
          <span class="setting-label">Monitor All</span>
          <span class="setting-value"
            >${this._renderBool(entry.monitor_all_namespaces)}</span
          >
        </div>
        ${!entry.monitor_all_namespaces && entry.namespaces.length > 0
          ? html`
              <div class="setting-row">
                <span class="setting-label">Selected</span>
                <span class="setting-value">
                  <div class="namespace-tags">
                    ${entry.namespaces.map(
                      (ns) => html`<span class="ns-tag">${ns}</span>`,
                    )}
                  </div>
                </span>
              </div>
            `
          : nothing}
        <div class="setting-row">
          <span class="setting-label">Device Grouping</span>
          <span class="setting-value"
            >${entry.device_grouping_mode === "namespace"
              ? "By Namespace"
              : "By Cluster"}</span
          >
        </div>
      </ha-card>
    `;
  }

  private _renderTimingCard(entry: ConfigEntry) {
    return html`
      <ha-card class="settings-card">
        <div class="card-title">
          <ha-icon icon="mdi:timer-cog"></ha-icon>
          Timing
        </div>
        <div class="setting-row">
          <span class="setting-label">Poll Interval</span>
          <span class="setting-value">${entry.switch_update_interval}s</span>
        </div>
        <div class="setting-row">
          <span class="setting-label">Scale Timeout</span>
          <span class="setting-value">${entry.scale_verification_timeout}s</span>
        </div>
        <div class="setting-row">
          <span class="setting-label">Scale Cooldown</span>
          <span class="setting-value">${entry.scale_cooldown}s</span>
        </div>
      </ha-card>
    `;
  }

  private _renderFeaturesCard(entry: ConfigEntry) {
    return html`
      <ha-card class="settings-card">
        <div class="card-title">
          <ha-icon icon="mdi:flask"></ha-icon>
          Features
        </div>
        <div class="setting-row">
          <span class="setting-label">Sidebar Panel</span>
          <span class="setting-value">${this._renderBool(entry.panel_enabled)}</span>
        </div>
        <div class="setting-row">
          <span class="setting-label">Watch API</span>
          <span class="setting-value">${this._renderBool(entry.watch_enabled)}</span>
        </div>
      </ha-card>
    `;
  }

  private _renderBool(value: boolean) {
    if (value) {
      return html`
        <span class="setting-value-bool bool-true">
          <ha-icon icon="mdi:check-circle"></ha-icon> Enabled
        </span>
      `;
    }
    return html`
      <span class="setting-value-bool bool-false">
        <ha-icon icon="mdi:close-circle-outline"></ha-icon> Disabled
      </span>
    `;
  }
}
