import { html, css, nothing } from "lit";
import { customElement } from "lit/decorators.js";
import { K8sDataView } from "./base-view";
import { stateStyles, badgeStyles } from "../styles/shared";

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
export class K8sSettings extends K8sDataView<ConfigResponse> {
  protected pollMs = 0;
  protected subscribe = false;
  protected loadErrorFallback = "Failed to load configuration";
  protected emptyMessage = "No Kubernetes entries configured.";

  protected async fetchData(): Promise<void> {
    const result: ConfigResponse = await this.hass.callWS({
      type: "kubernetes/config/list",
    });
    this._data = result;
  }

  private _navigateToIntegration(): void {
    window.open("/config/integrations/integration/kubernetes", "_blank");
  }

  static styles = [
    stateStyles,
    badgeStyles,
    css`
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
        color: var(--success-color, #4caf50);
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
    `,
  ];

  protected render() {
    const state = this.renderState(!this._data?.entries.length);
    if (state !== nothing) return state;

    return html`${this._data!.entries.map((e) => this._renderEntry(e))}`;
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
        ${
          !entry.monitor_all_namespaces && entry.namespaces.length > 0
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
            : nothing
        }
        <div class="setting-row">
          <span class="setting-label">Device Grouping</span>
          <span class="setting-value"
            >${
              entry.device_grouping_mode === "namespace" ? "By Namespace" : "By Cluster"
            }</span
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
        <div class="setting-row">
          <span class="setting-label">Update Mode</span>
          <span class="setting-value"
            >${entry.watch_enabled ? "Watch (real-time)" : "Polling"}</span
          >
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
