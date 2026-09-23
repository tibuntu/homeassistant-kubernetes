import { html, css, nothing } from "lit";
import { customElement, state } from "lit/decorators.js";
import { K8sDataView } from "./base-view";
import { stateStyles, badgeStyles } from "../styles/shared";
import { formatRelative, toggleInSet, CONDITION_LABELS } from "../utils/format";

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
  ingresses: "mdi:earth",
  services: "mdi:swap-horizontal",
};

const RESOURCE_LABELS: Record<string, string> = {
  pods: "Pods",
  nodes: "Nodes",
  deployments: "Deployments",
  statefulsets: "StatefulSets",
  daemonsets: "DaemonSets",
  cronjobs: "CronJobs",
  jobs: "Jobs",
  ingresses: "Ingresses",
  services: "Services",
};

@customElement("k8s-overview")
export class K8sOverview extends K8sDataView<OverviewResponse> {
  @state() private _expandedNamespaces: Set<string> = new Set();

  protected loadErrorFallback = "Failed to load cluster data";

  protected async fetchData(): Promise<void> {
    const result: OverviewResponse = await this.hass.callWS({
      type: "kubernetes/cluster/overview",
    });
    this._data = result;
  }

  private _toggleNamespaces(clusterId: string): void {
    this._expandedNamespaces = toggleInSet(this._expandedNamespaces, clusterId);
  }

  static styles = [
    stateStyles,
    badgeStyles,
    css`
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
    `,
  ];

  protected render() {
    const state = this.renderState(!this._data?.clusters.length);
    if (state !== nothing) return state;

    return html` ${this._data!.clusters.map((c) => this._renderCluster(c))} `;
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
        </div>

        <div class="meta-row">
          <div class="meta-item">
            <ha-icon icon="mdi:update"></ha-icon>
            <span>Updated ${formatRelative(cluster.last_update)}</span>
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
          ${
            totalAlerts > 0
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
                `
          }
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

  private _renderNamespaceSection(cluster: ClusterOverview) {
    const nsEntries = Object.entries(cluster.namespaces);
    if (nsEntries.length === 0) return nothing;

    const expanded = this._expandedNamespaces.has(cluster.entry_id);

    return html`
      <div
        class="section-header"
        role="button"
        tabindex="0"
        @click=${() => this._toggleNamespaces(cluster.entry_id)}
        @keydown=${(e: KeyboardEvent) => {
          if (e.key === "Enter" || e.key === " ") {
            e.preventDefault();
            this._toggleNamespaces(cluster.entry_id);
          }
        }}
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
