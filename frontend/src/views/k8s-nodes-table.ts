import { LitElement, html, css, nothing, PropertyValues } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import type { HomeAssistant } from "../types/homeassistant";

interface NodeData {
  name: string;
  status: string;
  internal_ip: string;
  external_ip: string;
  cpu_cores: number;
  cpu_usage_millicores?: number;
  memory_capacity_gib: number;
  memory_allocatable_gib: number;
  memory_usage_mib?: number;
  os_image: string;
  kernel_version: string;
  container_runtime: string;
  kubelet_version: string;
  schedulable: boolean;
  creation_timestamp: string;
  memory_pressure: boolean;
  disk_pressure: boolean;
  pid_pressure: boolean;
  network_unavailable: boolean;
}

interface ClusterNodes {
  entry_id: string;
  cluster_name: string;
  nodes: NodeData[];
}

interface NodesResponse {
  clusters: ClusterNodes[];
}

const CONDITION_LABELS: Record<string, string> = {
  memory_pressure: "Memory Pressure",
  disk_pressure: "Disk Pressure",
  pid_pressure: "PID Pressure",
  network_unavailable: "Network Unavailable",
};

@customElement("k8s-nodes-table")
export class K8sNodesTable extends LitElement {
  @property({ attribute: false }) public hass!: HomeAssistant;

  @state() private _data: NodesResponse | null = null;
  @state() private _loading = true;
  @state() private _error: string | null = null;
  @state() private _expandedNodes: Set<string> = new Set();
  @state() private _statusFilter: string = "all";
  @state() private _searchQuery: string = "";

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
      const result: NodesResponse = await this.hass.callWS({
        type: "kubernetes/nodes/list",
      });
      this._data = result;
    } catch (err: any) {
      this._error = err.message || "Failed to load nodes data";
    } finally {
      this._loading = false;
      this._loadingInFlight = false;
    }
  }

  private _toggleNode(nodeKey: string): void {
    const updated = new Set(this._expandedNodes);
    if (updated.has(nodeKey)) {
      updated.delete(nodeKey);
    } else {
      updated.add(nodeKey);
    }
    this._expandedNodes = updated;
  }

  private _getConditions(node: NodeData): string[] {
    const conditions: string[] = [];
    if (node.memory_pressure) conditions.push("memory_pressure");
    if (node.disk_pressure) conditions.push("disk_pressure");
    if (node.pid_pressure) conditions.push("pid_pressure");
    if (node.network_unavailable) conditions.push("network_unavailable");
    return conditions;
  }

  private _formatAge(timestamp: string): string {
    if (!timestamp || timestamp === "N/A") return "N/A";
    const created = new Date(timestamp).getTime();
    const now = Date.now();
    const diff = Math.max(0, Math.floor((now - created) / 1000));
    if (diff < 60) return `${diff}s`;
    if (diff < 3600) return `${Math.floor(diff / 60)}m`;
    if (diff < 86400) return `${Math.floor(diff / 3600)}h`;
    return `${Math.floor(diff / 86400)}d`;
  }

  private _getFilteredNodes(nodes: NodeData[]): NodeData[] {
    let filtered = nodes;

    if (this._statusFilter !== "all") {
      filtered = filtered.filter((n) =>
        this._statusFilter === "ready" ? n.status === "Ready" : n.status !== "Ready",
      );
    }

    if (this._searchQuery) {
      const q = this._searchQuery.toLowerCase();
      filtered = filtered.filter(
        (n) =>
          n.name.toLowerCase().includes(q) ||
          n.internal_ip.toLowerCase().includes(q) ||
          n.kubelet_version.toLowerCase().includes(q),
      );
    }

    return filtered;
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

    .cluster-name {
      font-size: 20px;
      font-weight: 500;
      color: var(--primary-text-color);
      margin-bottom: 12px;
    }

    .filters {
      display: flex;
      gap: 12px;
      margin-bottom: 16px;
      flex-wrap: wrap;
      align-items: center;
    }

    .search-input {
      padding: 8px 12px;
      border: 1px solid var(--divider-color);
      border-radius: 8px;
      background: var(--card-background-color, var(--primary-background-color));
      color: var(--primary-text-color);
      font-size: 14px;
      min-width: 200px;
    }

    .search-input:focus {
      outline: none;
      border-color: var(--primary-color);
    }

    .filter-chip {
      display: inline-flex;
      align-items: center;
      padding: 6px 14px;
      border-radius: 16px;
      font-size: 13px;
      cursor: pointer;
      border: 1px solid var(--divider-color);
      background: transparent;
      color: var(--primary-text-color);
      user-select: none;
      transition:
        background 0.2s,
        border-color 0.2s;
    }

    .filter-chip:hover {
      background: rgba(var(--rgb-primary-color, 3, 169, 244), 0.08);
    }

    .filter-chip[active] {
      background: rgba(var(--rgb-primary-color, 3, 169, 244), 0.15);
      border-color: var(--primary-color);
      color: var(--primary-color);
    }

    .node-card {
      margin-bottom: 8px;
      border-radius: 12px;
      overflow: hidden;
    }

    .node-row {
      display: grid;
      grid-template-columns: 1fr auto auto auto auto auto;
      align-items: center;
      gap: 16px;
      padding: 12px 16px;
      cursor: pointer;
      font-size: 14px;
      transition: background 0.15s;
    }

    .node-row:hover {
      background: rgba(var(--rgb-primary-color, 3, 169, 244), 0.04);
    }

    .node-name {
      font-weight: 500;
      display: flex;
      align-items: center;
      gap: 8px;
      --mdc-icon-size: 18px;
    }

    .badge {
      display: inline-flex;
      align-items: center;
      gap: 4px;
      padding: 2px 10px;
      border-radius: 12px;
      font-size: 12px;
      font-weight: 500;
      white-space: nowrap;
    }

    .badge-ready {
      background: rgba(var(--rgb-success-color, 76, 175, 80), 0.15);
      color: var(--success-color, #4caf50);
    }

    .badge-not-ready {
      background: rgba(var(--rgb-error-color, 244, 67, 54), 0.15);
      color: var(--error-color, #f44336);
    }

    .badge-unschedulable {
      background: rgba(var(--rgb-warning-color, 255, 152, 0), 0.15);
      color: var(--warning-color, #ff9800);
    }

    .badge-condition {
      background: rgba(var(--rgb-warning-color, 255, 152, 0), 0.15);
      color: var(--warning-color, #ff9800);
    }

    .node-ip {
      color: var(--secondary-text-color);
      font-size: 13px;
      font-family: monospace;
    }

    .node-resources {
      display: flex;
      align-items: center;
      gap: 12px;
      font-size: 13px;
      color: var(--secondary-text-color);
      --mdc-icon-size: 16px;
    }

    .node-age {
      font-size: 13px;
      color: var(--secondary-text-color);
    }

    .node-details {
      padding: 0 16px 16px;
    }

    .details-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
      gap: 12px;
    }

    .detail-item {
      display: flex;
      flex-direction: column;
      gap: 2px;
    }

    .detail-label {
      font-size: 12px;
      color: var(--secondary-text-color);
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }

    .detail-value {
      font-size: 14px;
      color: var(--primary-text-color);
    }

    .detail-value.mono {
      font-family: monospace;
    }

    .conditions-row {
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
      margin-top: 8px;
    }

    .resource-bar-container {
      display: flex;
      align-items: center;
      gap: 6px;
    }

    .resource-label {
      font-size: 11px;
      font-weight: 500;
      color: var(--secondary-text-color);
      min-width: 28px;
    }

    .resource-bar {
      width: 60px;
      height: 6px;
      background: var(--divider-color);
      border-radius: 3px;
      overflow: hidden;
    }

    .resource-bar-fill {
      height: 100%;
      border-radius: 3px;
      background: var(--primary-color);
    }

    .resource-bar-fill.bar-warn {
      background: var(--warning-color, #ff9800);
    }

    .node-count {
      font-size: 13px;
      color: var(--secondary-text-color);
      margin-bottom: 8px;
    }

    @media (max-width: 768px) {
      .node-row {
        grid-template-columns: 1fr auto;
        gap: 8px;
      }

      .node-ip,
      .node-resources,
      .node-age {
        display: none;
      }
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
      return html`<div class="empty">No Kubernetes clusters configured.</div>`;
    }

    return html`${this._data.clusters.map((c) => this._renderCluster(c))}`;
  }

  private _renderCluster(cluster: ClusterNodes) {
    const filtered = this._getFilteredNodes(cluster.nodes);
    const readyCount = cluster.nodes.filter((n) => n.status === "Ready").length;

    return html`
      <div class="cluster-section">
        ${this._data!.clusters.length > 1
          ? html`<div class="cluster-name">${cluster.cluster_name}</div>`
          : nothing}

        <div class="filters">
          <input
            class="search-input"
            type="text"
            placeholder="Search nodes..."
            .value=${this._searchQuery}
            @input=${(e: Event) => {
              this._searchQuery = (e.target as HTMLInputElement).value;
            }}
          />
          ${(["all", "ready", "not-ready"] as const).map(
            (f) => html`
              <button
                class="filter-chip"
                ?active=${this._statusFilter === f}
                @click=${() => {
                  this._statusFilter = f;
                }}
              >
                ${f === "all" ? "All" : f === "ready" ? "Ready" : "Not Ready"}
              </button>
            `,
          )}
        </div>

        <div class="node-count">
          ${readyCount}/${cluster.nodes.length} nodes ready
          ${filtered.length !== cluster.nodes.length
            ? html` &middot; showing ${filtered.length}`
            : nothing}
        </div>

        ${filtered.length === 0
          ? html`<div class="empty">No nodes match your filters.</div>`
          : filtered.map((node) => this._renderNode(cluster.entry_id, node))}
      </div>
    `;
  }

  private _renderNode(entryId: string, node: NodeData) {
    const nodeKey = `${entryId}_${node.name}`;
    const expanded = this._expandedNodes.has(nodeKey);
    const conditions = this._getConditions(node);

    const hasMetrics =
      node.cpu_usage_millicores != null && node.memory_usage_mib != null;
    const cpuCapacityMillicores = node.cpu_cores * 1000;
    const cpuPercent = hasMetrics
      ? Math.round((node.cpu_usage_millicores! / cpuCapacityMillicores) * 100)
      : 0;
    const memUsageGib = hasMetrics ? node.memory_usage_mib! / 1024 : 0;
    const memPercent = hasMetrics
      ? Math.round((memUsageGib / node.memory_capacity_gib) * 100)
      : 0;

    return html`
      <ha-card class="node-card">
        <div class="node-row" @click=${() => this._toggleNode(nodeKey)}>
          <div class="node-name">
            <ha-icon
              icon=${expanded ? "mdi:chevron-down" : "mdi:chevron-right"}
            ></ha-icon>
            ${node.name}
            ${!node.schedulable
              ? html`<span class="badge badge-unschedulable">Unschedulable</span>`
              : nothing}
            ${conditions.length > 0
              ? html`<span class="badge badge-condition"
                  >${conditions.length}
                  condition${conditions.length > 1 ? "s" : ""}</span
                >`
              : nothing}
          </div>
          <span
            class="badge ${node.status === "Ready" ? "badge-ready" : "badge-not-ready"}"
          >
            ${node.status}
          </span>
          <span class="node-ip">${node.internal_ip}</span>
          <div class="node-resources">
            ${hasMetrics
              ? html`
                  <div class="resource-bar-container" title="CPU usage">
                    <span class="resource-label">CPU</span>
                    <div class="resource-bar">
                      <div
                        class="resource-bar-fill ${cpuPercent > 80 ? "bar-warn" : ""}"
                        style="width: ${Math.min(cpuPercent, 100)}%"
                      ></div>
                    </div>
                    <span>${cpuPercent}%</span>
                  </div>
                  <div class="resource-bar-container" title="Memory usage">
                    <span class="resource-label">MEM</span>
                    <div class="resource-bar">
                      <div
                        class="resource-bar-fill ${memPercent > 80 ? "bar-warn" : ""}"
                        style="width: ${Math.min(memPercent, 100)}%"
                      ></div>
                    </div>
                    <span>${memPercent}%</span>
                  </div>
                `
              : html`<span
                  >${node.cpu_cores} CPU &middot; ${node.memory_capacity_gib} GiB</span
                >`}
          </div>
          <span class="node-age">${this._formatAge(node.creation_timestamp)}</span>
        </div>
        ${expanded ? this._renderNodeDetails(node, conditions) : nothing}
      </ha-card>
    `;
  }

  private _renderNodeDetails(node: NodeData, conditions: string[]) {
    const hasMetrics =
      node.cpu_usage_millicores != null && node.memory_usage_mib != null;
    const memUsageGib = hasMetrics
      ? Math.round((node.memory_usage_mib! / 1024) * 100) / 100
      : null;

    return html`
      <div class="node-details">
        <div class="details-grid">
          <div class="detail-item">
            <span class="detail-label">Internal IP</span>
            <span class="detail-value mono">${node.internal_ip}</span>
          </div>
          <div class="detail-item">
            <span class="detail-label">External IP</span>
            <span class="detail-value mono">${node.external_ip}</span>
          </div>
          <div class="detail-item">
            <span class="detail-label">CPU Cores</span>
            <span class="detail-value">${node.cpu_cores}</span>
          </div>
          ${hasMetrics
            ? html`
                <div class="detail-item">
                  <span class="detail-label">CPU Usage</span>
                  <span class="detail-value"
                    >${node.cpu_usage_millicores}m / ${node.cpu_cores * 1000}m</span
                  >
                </div>
              `
            : nothing}
          <div class="detail-item">
            <span class="detail-label">Memory Capacity</span>
            <span class="detail-value">${node.memory_capacity_gib} GiB</span>
          </div>
          <div class="detail-item">
            <span class="detail-label">Memory Allocatable</span>
            <span class="detail-value">${node.memory_allocatable_gib} GiB</span>
          </div>
          ${hasMetrics
            ? html`
                <div class="detail-item">
                  <span class="detail-label">Memory Usage</span>
                  <span class="detail-value"
                    >${memUsageGib} / ${node.memory_capacity_gib} GiB</span
                  >
                </div>
              `
            : nothing}
          <div class="detail-item">
            <span class="detail-label">OS Image</span>
            <span class="detail-value">${node.os_image}</span>
          </div>
          <div class="detail-item">
            <span class="detail-label">Kernel</span>
            <span class="detail-value mono">${node.kernel_version}</span>
          </div>
          <div class="detail-item">
            <span class="detail-label">Container Runtime</span>
            <span class="detail-value">${node.container_runtime}</span>
          </div>
          <div class="detail-item">
            <span class="detail-label">Kubelet Version</span>
            <span class="detail-value mono">${node.kubelet_version}</span>
          </div>
          <div class="detail-item">
            <span class="detail-label">Schedulable</span>
            <span class="detail-value">${node.schedulable ? "Yes" : "No"}</span>
          </div>
          <div class="detail-item">
            <span class="detail-label">Created</span>
            <span class="detail-value">${node.creation_timestamp}</span>
          </div>
        </div>
        ${conditions.length > 0
          ? html`
              <div class="conditions-row">
                ${conditions.map(
                  (c) => html`
                    <span class="badge badge-condition">
                      ${CONDITION_LABELS[c] || c}
                    </span>
                  `,
                )}
              </div>
            `
          : nothing}
      </div>
    `;
  }
}
