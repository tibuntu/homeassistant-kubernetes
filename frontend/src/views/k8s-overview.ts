import { LitElement, html, css, nothing, PropertyValues } from "lit";
import { customElement, property, state } from "lit/decorators.js";

interface AlertNodePressure {
  name: string;
  conditions: string[];
}

interface AlertDegradedWorkload {
  name: string;
  type: string;
  namespace: string;
  ready: number;
  desired: number;
}

interface AlertFailedPod {
  name: string;
  namespace: string;
  phase: string;
}

interface ClusterAlerts {
  nodes_with_pressure: AlertNodePressure[];
  degraded_workloads: AlertDegradedWorkload[];
  failed_pods: AlertFailedPod[];
}

interface ClusterOverview {
  entry_id: string;
  cluster_name: string;
  healthy: boolean | null;
  watch_enabled: boolean;
  last_update: number;
  counts: Record<string, number>;
  namespaces: Record<string, Record<string, number>>;
  alerts: ClusterAlerts;
}

interface OverviewResponse {
  clusters: ClusterOverview[];
}

const RESOURCE_ICONS: Record<string, string> = {
  pods: "mdi:cube-outline",
  nodes: "mdi:server",
  deployments: "mdi:rocket-launch",
  statefulsets: "mdi:database",
  daemonsets: "mdi:lan",
  cronjobs: "mdi:clock-outline",
  jobs: "mdi:briefcase-check",
};

const RESOURCE_LABELS: Record<string, string> = {
  pods: "Pods",
  nodes: "Nodes",
  deployments: "Deployments",
  statefulsets: "StatefulSets",
  daemonsets: "DaemonSets",
  cronjobs: "CronJobs",
  jobs: "Jobs",
};

const CONDITION_LABELS: Record<string, string> = {
  memory_pressure: "Memory Pressure",
  disk_pressure: "Disk Pressure",
  pid_pressure: "PID Pressure",
  network_unavailable: "Network Unavailable",
};

@customElement("k8s-overview")
export class K8sOverview extends LitElement {
  @property({ attribute: false }) public hass!: any;

  @state() private _data: OverviewResponse | null = null;
  @state() private _loading = true;
  @state() private _error: string | null = null;
  @state() private _expandedNamespaces: Set<string> = new Set();

  private _refreshInterval?: ReturnType<typeof setInterval>;
  private _loadingInFlight = false;
  private _boundVisibilityHandler = this._handleVisibilityChange.bind(this);

  protected firstUpdated(_changedProps: PropertyValues): void {
    this._loadData();
    this._startPolling();
    document.addEventListener("visibilitychange", this._boundVisibilityHandler);
  }

  disconnectedCallback(): void {
    super.disconnectedCallback();
    this._stopPolling();
    document.removeEventListener("visibilitychange", this._boundVisibilityHandler);
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
      this._refreshInterval = setInterval(() => this._loadData(), 30000);
    }
  }

  private _stopPolling(): void {
    if (this._refreshInterval) {
      clearInterval(this._refreshInterval);
      this._refreshInterval = undefined;
    }
  }

  private async _loadData(): Promise<void> {
    if (this._loadingInFlight) return;
    this._loadingInFlight = true;
    if (!this._data) {
      this._loading = true;
    }
    this._error = null;
    try {
      const result: OverviewResponse = await this.hass.callWS({
        type: "kubernetes/cluster/overview",
      });
      this._data = result;
    } catch (err: any) {
      this._error = err.message || "Failed to load cluster data";
    } finally {
      this._loading = false;
      this._loadingInFlight = false;
    }
  }

  private _toggleNamespaces(clusterId: string): void {
    const updated = new Set(this._expandedNamespaces);
    if (updated.has(clusterId)) {
      updated.delete(clusterId);
    } else {
      updated.add(clusterId);
    }
    this._expandedNamespaces = updated;
  }

  private _formatRelativeTime(timestamp: number): string {
    if (!timestamp) return "Never";
    const now = Date.now() / 1000;
    const diff = Math.max(0, Math.floor(now - timestamp));
    if (diff < 60) return `${diff}s ago`;
    if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
    if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
    return `${Math.floor(diff / 86400)}d ago`;
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

    .cluster-section {
      margin-bottom: 24px;
    }

    .cluster-header {
      display: flex;
      align-items: center;
      gap: 12px;
      margin-bottom: 16px;
      flex-wrap: wrap;
    }

    .cluster-name {
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
      background: rgba(var(--rgb-success-color, 76, 175, 80), 0.15);
      color: var(--success-color, #4caf50);
    }

    .badge-unhealthy {
      background: rgba(var(--rgb-error-color, 244, 67, 54), 0.15);
      color: var(--error-color, #f44336);
    }

    .badge-unknown {
      background: rgba(var(--rgb-disabled-color, 158, 158, 158), 0.15);
      color: var(--disabled-color, #9e9e9e);
    }

    .badge-watch {
      background: rgba(var(--rgb-info-color, 33, 150, 243), 0.15);
      color: var(--info-color, #2196f3);
    }

    .badge-watch-off {
      background: rgba(var(--rgb-disabled-color, 158, 158, 158), 0.1);
      color: var(--secondary-text-color);
    }

    .meta-row {
      display: flex;
      align-items: center;
      gap: 16px;
      margin-bottom: 16px;
      font-size: 13px;
      color: var(--secondary-text-color);
      flex-wrap: wrap;
    }

    .meta-item {
      display: flex;
      align-items: center;
      gap: 4px;
      --mdc-icon-size: 16px;
    }

    .refresh-btn {
      cursor: pointer;
      background: none;
      border: none;
      color: var(--primary-color);
      padding: 4px;
      border-radius: 50%;
      display: flex;
      align-items: center;
      --mdc-icon-size: 18px;
    }

    .refresh-btn:hover {
      background: rgba(var(--rgb-primary-color, 3, 169, 244), 0.1);
    }

    .counts-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
      gap: 12px;
      margin-bottom: 20px;
    }

    .count-card {
      padding: 16px;
      border-radius: 12px;
      text-align: center;
      --mdc-icon-size: 28px;
    }

    .count-card ha-icon {
      color: var(--primary-color);
      margin-bottom: 8px;
    }

    .count-value {
      font-size: 28px;
      font-weight: 500;
      color: var(--primary-text-color);
    }

    .count-label {
      font-size: 13px;
      color: var(--secondary-text-color);
      margin-top: 4px;
    }

    .section-header {
      display: flex;
      align-items: center;
      gap: 8px;
      cursor: pointer;
      user-select: none;
      padding: 8px 0;
      font-size: 16px;
      font-weight: 500;
      color: var(--primary-text-color);
      --mdc-icon-size: 20px;
    }

    .section-header:hover {
      color: var(--primary-color);
    }

    .ns-table {
      width: 100%;
      border-collapse: collapse;
      margin: 8px 0 16px;
      font-size: 13px;
    }

    .ns-table th {
      text-align: left;
      padding: 8px 12px;
      color: var(--secondary-text-color);
      font-weight: 500;
      border-bottom: 1px solid var(--divider-color);
    }

    .ns-table td {
      padding: 6px 12px;
      border-bottom: 1px solid var(--divider-color);
    }

    .ns-table tr:last-child td {
      border-bottom: none;
    }

    .alerts-section {
      margin-top: 16px;
    }

    .alert-card {
      display: flex;
      align-items: flex-start;
      gap: 12px;
      padding: 12px 16px;
      margin-bottom: 8px;
      border-radius: 8px;
      font-size: 14px;
      --mdc-icon-size: 20px;
    }

    .alert-warning {
      background: rgba(var(--rgb-warning-color, 255, 152, 0), 0.1);
      color: var(--primary-text-color);
    }

    .alert-warning ha-icon {
      color: var(--warning-color, #ff9800);
    }

    .alert-error {
      background: rgba(var(--rgb-error-color, 244, 67, 54), 0.1);
      color: var(--primary-text-color);
    }

    .alert-error ha-icon {
      color: var(--error-color, #f44336);
    }

    .alert-title {
      font-weight: 500;
    }

    .alert-detail {
      font-size: 13px;
      color: var(--secondary-text-color);
      margin-top: 2px;
    }

    .no-alerts {
      display: flex;
      align-items: center;
      gap: 12px;
      padding: 16px;
      border-radius: 8px;
      background: rgba(var(--rgb-success-color, 76, 175, 80), 0.08);
      font-size: 14px;
      --mdc-icon-size: 24px;
    }

    .no-alerts ha-icon {
      color: var(--success-color, #4caf50);
      flex-shrink: 0;
    }

    .no-alerts-text {
      flex: 1;
    }

    .no-alerts-title {
      font-weight: 500;
      color: var(--primary-text-color);
    }

    .no-alerts-detail {
      font-size: 12px;
      color: var(--secondary-text-color);
      margin-top: 2px;
    }

    .alerts-header {
      display: flex;
      align-items: center;
      gap: 8px;
      margin-bottom: 8px;
      font-size: 16px;
      font-weight: 500;
      color: var(--primary-text-color);
      --mdc-icon-size: 20px;
    }

    .alerts-info-icon {
      color: var(--secondary-text-color);
      cursor: help;
      --mdc-icon-size: 18px;
      position: relative;
    }

    .alerts-info-icon:hover {
      color: var(--primary-color);
    }

    .alerts-tooltip {
      display: none;
      position: absolute;
      bottom: calc(100% + 8px);
      left: 0;
      background: var(--card-background-color, #fff);
      border: 1px solid var(--divider-color);
      border-radius: 8px;
      padding: 12px 16px;
      font-size: 12px;
      font-weight: 400;
      color: var(--secondary-text-color);
      width: 280px;
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
      z-index: 10;
      line-height: 1.5;
    }

    .alerts-info-icon:hover .alerts-tooltip {
      display: block;
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

    if (!this._data?.clusters.length) {
      return html` <div class="empty">No Kubernetes clusters configured.</div> `;
    }

    return html` ${this._data.clusters.map((c) => this._renderCluster(c))} `;
  }

  private _renderCluster(cluster: ClusterOverview) {
    const totalAlerts =
      cluster.alerts.nodes_with_pressure.length +
      cluster.alerts.degraded_workloads.length +
      cluster.alerts.failed_pods.length;

    return html`
      <div class="cluster-section">
        <div class="cluster-header">
          <span class="cluster-name">${cluster.cluster_name}</span>
          ${this._renderHealthBadge(cluster.healthy)}
          ${this._renderWatchBadge(cluster.watch_enabled)}
        </div>

        <div class="meta-row">
          <div class="meta-item">
            <ha-icon icon="mdi:update"></ha-icon>
            <span>Updated ${this._formatRelativeTime(cluster.last_update)}</span>
          </div>
          <button class="refresh-btn" @click=${this._loadData} title="Refresh data">
            <ha-icon icon="mdi:refresh"></ha-icon>
          </button>
        </div>

        <div class="counts-grid">
          ${Object.entries(cluster.counts).map(
            ([key, count]) => html`
              <ha-card class="count-card">
                <ha-icon icon=${RESOURCE_ICONS[key] || "mdi:help"}></ha-icon>
                <div class="count-value">${count}</div>
                <div class="count-label">${RESOURCE_LABELS[key] || key}</div>
              </ha-card>
            `,
          )}
        </div>

        <div class="alerts-section">
          <div class="alerts-header">
            <ha-icon icon="mdi:bell-outline"></ha-icon>
            <span>Alerts${totalAlerts > 0 ? ` (${totalAlerts})` : ""}</span>
            <span class="alerts-info-icon">
              <ha-icon icon="mdi:information-outline"></ha-icon>
              <div class="alerts-tooltip">
                Alerts monitor your cluster for issues that may need attention: nodes
                experiencing memory, disk, or PID pressure; workloads with fewer ready
                replicas than desired; and pods in a failed state.
              </div>
            </span>
          </div>
          ${totalAlerts > 0
            ? this._renderAlerts(cluster.alerts)
            : html`
                <div class="no-alerts">
                  <ha-icon icon="mdi:check-circle"></ha-icon>
                  <div class="no-alerts-text">
                    <div class="no-alerts-title">No active alerts</div>
                    <div class="no-alerts-detail">
                      All nodes, workloads, and pods are operating normally.
                    </div>
                  </div>
                </div>
              `}
        </div>

        ${this._renderNamespaceSection(cluster)}
      </div>
    `;
  }

  private _renderHealthBadge(healthy: boolean | null) {
    if (healthy === true) {
      return html`<span class="badge badge-healthy">Healthy</span>`;
    }
    if (healthy === false) {
      return html`<span class="badge badge-unhealthy">Unhealthy</span>`;
    }
    return html`<span class="badge badge-unknown">Unknown</span>`;
  }

  private _renderWatchBadge(enabled: boolean) {
    if (enabled) {
      return html`
        <span class="badge badge-watch">
          <ha-icon icon="mdi:eye"></ha-icon> Watch Active
        </span>
      `;
    }
    return html`
      <span class="badge badge-watch-off">
        <ha-icon icon="mdi:eye-off"></ha-icon> Polling
      </span>
    `;
  }

  private _renderNamespaceSection(cluster: ClusterOverview) {
    const nsEntries = Object.entries(cluster.namespaces);
    if (nsEntries.length === 0) return nothing;

    const expanded = this._expandedNamespaces.has(cluster.entry_id);

    return html`
      <div
        class="section-header"
        @click=${() => this._toggleNamespaces(cluster.entry_id)}
      >
        <ha-icon icon=${expanded ? "mdi:chevron-down" : "mdi:chevron-right"}></ha-icon>
        <span>Namespaces (${nsEntries.length})</span>
      </div>
      ${expanded ? this._renderNamespaceTable(nsEntries) : nothing}
    `;
  }

  private _renderNamespaceTable(nsEntries: [string, Record<string, number>][]) {
    const columns = [
      "pods",
      "deployments",
      "statefulsets",
      "daemonsets",
      "cronjobs",
      "jobs",
    ];

    return html`
      <table class="ns-table">
        <thead>
          <tr>
            <th>Namespace</th>
            ${columns.map((col) => html`<th>${RESOURCE_LABELS[col] || col}</th>`)}
          </tr>
        </thead>
        <tbody>
          ${nsEntries
            .sort(([a], [b]) => a.localeCompare(b))
            .map(
              ([ns, counts]) => html`
                <tr>
                  <td>${ns}</td>
                  ${columns.map((col) => html`<td>${counts[col] || 0}</td>`)}
                </tr>
              `,
            )}
        </tbody>
      </table>
    `;
  }

  private _renderAlerts(alerts: ClusterAlerts) {
    return html`
      ${alerts.nodes_with_pressure.map(
        (node) => html`
          <div class="alert-card alert-warning">
            <ha-icon icon="mdi:server-network-off"></ha-icon>
            <div>
              <div class="alert-title">Node: ${node.name}</div>
              <div class="alert-detail">
                ${node.conditions.map((c) => CONDITION_LABELS[c] || c).join(", ")}
              </div>
            </div>
          </div>
        `,
      )}
      ${alerts.degraded_workloads.map(
        (wl) => html`
          <div class="alert-card alert-warning">
            <ha-icon icon="mdi:alert"></ha-icon>
            <div>
              <div class="alert-title">${wl.type}: ${wl.namespace}/${wl.name}</div>
              <div class="alert-detail">${wl.ready}/${wl.desired} replicas ready</div>
            </div>
          </div>
        `,
      )}
      ${alerts.failed_pods.map(
        (pod) => html`
          <div class="alert-card alert-error">
            <ha-icon icon="mdi:alert-octagon"></ha-icon>
            <div>
              <div class="alert-title">Pod: ${pod.namespace}/${pod.name}</div>
              <div class="alert-detail">Phase: ${pod.phase}</div>
            </div>
          </div>
        `,
      )}
    `;
  }
}
