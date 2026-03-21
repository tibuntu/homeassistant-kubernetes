import { LitElement, html, css, nothing, PropertyValues } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import type { HomeAssistant } from "../types/homeassistant";

interface PodData {
  name: string;
  namespace: string;
  phase: string;
  ready_containers: number;
  total_containers: number;
  restart_count: number;
  node_name: string;
  pod_ip: string;
  creation_timestamp: string;
  owner_kind: string;
  owner_name: string;
}

interface PodIdentifier {
  entry_id: string;
  pod_name: string;
  namespace: string;
}

interface ClusterPods {
  entry_id: string;
  cluster_name: string;
  pods: PodData[];
}

interface PodsResponse {
  clusters: ClusterPods[];
}

const PHASE_CLASSES: Record<string, string> = {
  Running: "badge-running",
  Succeeded: "badge-succeeded",
  Pending: "badge-pending",
  Failed: "badge-failed",
  Unknown: "badge-unknown",
};

@customElement("k8s-pods-table")
export class K8sPodsTable extends LitElement {
  @property({ attribute: false }) public hass!: HomeAssistant;

  @state() private _data: PodsResponse | null = null;
  @state() private _loading = true;
  @state() private _error: string | null = null;
  @state() private _searchQuery: string = "";
  @state() private _phaseFilter: string = "all";
  @state() private _namespaceFilter: string = "all";
  @state() private _sortField: string = "name";
  @state() private _sortAsc: boolean = true;
  @state() private _deleteConfirm: PodIdentifier | null = null;
  @state() private _deleting = false;

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
      const result: PodsResponse = await this.hass.callWS({
        type: "kubernetes/pods/list",
      });
      this._data = result;
    } catch (err: any) {
      this._error = err.message || "Failed to load pods data";
    } finally {
      this._loading = false;
      this._loadingInFlight = false;
    }
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

  private _getNamespaces(pods: PodData[]): string[] {
    return [...new Set(pods.map((p) => p.namespace))].sort();
  }

  private _getFilteredPods(pods: PodData[]): PodData[] {
    let filtered = pods;

    if (this._phaseFilter !== "all") {
      filtered = filtered.filter((p) => p.phase === this._phaseFilter);
    }

    if (this._namespaceFilter !== "all") {
      filtered = filtered.filter((p) => p.namespace === this._namespaceFilter);
    }

    if (this._searchQuery) {
      const q = this._searchQuery.toLowerCase();
      filtered = filtered.filter(
        (p) =>
          p.name.toLowerCase().includes(q) ||
          p.namespace.toLowerCase().includes(q) ||
          p.node_name.toLowerCase().includes(q) ||
          p.owner_name.toLowerCase().includes(q),
      );
    }

    filtered.sort((a, b) => {
      let valA: string | number;
      let valB: string | number;
      const field = this._sortField;
      if (field === "restarts") {
        valA = a.restart_count;
        valB = b.restart_count;
      } else if (field === "age") {
        valA = a.creation_timestamp || "";
        valB = b.creation_timestamp || "";
      } else {
        valA = (a as any)[field] || "";
        valB = (b as any)[field] || "";
      }
      const cmp = valA < valB ? -1 : valA > valB ? 1 : 0;
      return this._sortAsc ? cmp : -cmp;
    });

    return filtered;
  }

  private _handleSort(field: string): void {
    if (this._sortField === field) {
      this._sortAsc = !this._sortAsc;
    } else {
      this._sortField = field;
      this._sortAsc = true;
    }
  }

  private _requestDelete(entryId: string, pod: PodData): void {
    this._deleteConfirm = {
      entry_id: entryId,
      pod_name: pod.name,
      namespace: pod.namespace,
    };
  }

  private _cancelDelete(): void {
    this._deleteConfirm = null;
  }

  private async _confirmDelete(): Promise<void> {
    if (!this._deleteConfirm) return;
    this._deleting = true;
    try {
      await this.hass.callWS({
        type: "kubernetes/pods/delete",
        entry_id: this._deleteConfirm.entry_id,
        pod_name: this._deleteConfirm.pod_name,
        namespace: this._deleteConfirm.namespace,
      });
      this._deleteConfirm = null;
      await this._loadData();
    } catch (err: any) {
      this._error = err.message || "Failed to delete pod";
      this._deleteConfirm = null;
    } finally {
      this._deleting = false;
    }
  }

  private _sortIcon(field: string): string {
    if (this._sortField !== field) return "";
    return this._sortAsc ? "mdi:arrow-up" : "mdi:arrow-down";
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

    select.ns-select {
      padding: 6px 12px;
      border: 1px solid var(--divider-color);
      border-radius: 8px;
      background: var(--card-background-color, var(--primary-background-color));
      color: var(--primary-text-color);
      font-size: 13px;
    }

    .pod-count {
      font-size: 13px;
      color: var(--secondary-text-color);
      margin-bottom: 8px;
    }

    .pods-table {
      width: 100%;
      border-collapse: collapse;
      font-size: 13px;
    }

    .pods-table th {
      text-align: left;
      padding: 10px 12px;
      color: var(--secondary-text-color);
      font-weight: 500;
      border-bottom: 2px solid var(--divider-color);
      cursor: pointer;
      user-select: none;
      white-space: nowrap;
      --mdc-icon-size: 14px;
    }

    .pods-table th:hover {
      color: var(--primary-color);
    }

    .pods-table th ha-icon {
      vertical-align: middle;
      margin-left: 2px;
    }

    .pods-table td {
      padding: 8px 12px;
      border-bottom: 1px solid var(--divider-color);
      vertical-align: middle;
    }

    .pods-table tr:last-child td {
      border-bottom: none;
    }

    .pods-table tr:hover td {
      background: rgba(var(--rgb-primary-color, 3, 169, 244), 0.04);
    }

    .badge {
      display: inline-flex;
      align-items: center;
      padding: 2px 10px;
      border-radius: 12px;
      font-size: 12px;
      font-weight: 500;
      white-space: nowrap;
    }

    .badge-running {
      background: rgba(var(--rgb-success-color, 76, 175, 80), 0.15);
      color: var(--success-color, #4caf50);
    }

    .badge-succeeded {
      background: rgba(var(--rgb-info-color, 33, 150, 243), 0.15);
      color: var(--info-color, #2196f3);
    }

    .badge-pending {
      background: rgba(var(--rgb-warning-color, 255, 152, 0), 0.15);
      color: var(--warning-color, #ff9800);
    }

    .badge-failed {
      background: rgba(var(--rgb-error-color, 244, 67, 54), 0.15);
      color: var(--error-color, #f44336);
    }

    .badge-unknown {
      background: rgba(var(--rgb-disabled-color, 158, 158, 158), 0.15);
      color: var(--disabled-color, #9e9e9e);
    }

    .mono {
      font-family: monospace;
    }

    .pod-name {
      font-weight: 500;
      word-break: break-all;
    }

    .owner-info {
      font-size: 12px;
      color: var(--secondary-text-color);
    }

    .restart-warn {
      color: var(--warning-color, #ff9800);
      font-weight: 500;
    }

    .col-actions {
      width: 40px;
      min-width: 40px;
      cursor: default;
    }

    .delete-btn {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      background: transparent;
      border: none;
      cursor: pointer;
      padding: 4px;
      border-radius: 50%;
      color: var(--secondary-text-color);
      --mdc-icon-size: 18px;
      transition:
        color 0.2s,
        background 0.2s;
    }

    .delete-btn:hover {
      color: var(--error-color, #f44336);
      background: rgba(var(--rgb-error-color, 244, 67, 54), 0.1);
    }

    .confirm-overlay {
      position: fixed;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
      background: rgba(0, 0, 0, 0.5);
      display: flex;
      align-items: center;
      justify-content: center;
      z-index: 999;
    }

    .confirm-dialog {
      background: var(--card-background-color, #fff);
      border-radius: 12px;
      padding: 24px;
      max-width: 400px;
      width: 90%;
      box-shadow: 0 4px 24px rgba(0, 0, 0, 0.3);
    }

    .confirm-dialog h3 {
      margin: 0 0 12px;
      font-size: 18px;
      color: var(--primary-text-color);
    }

    .confirm-dialog p {
      margin: 0 0 20px;
      color: var(--secondary-text-color);
      font-size: 14px;
    }

    .confirm-dialog .pod-ref {
      font-family: monospace;
      font-weight: 500;
      color: var(--primary-text-color);
    }

    .confirm-actions {
      display: flex;
      justify-content: flex-end;
      gap: 8px;
    }

    .confirm-actions button {
      padding: 8px 20px;
      border-radius: 4px;
      font-size: 14px;
      cursor: pointer;
      border: 1px solid var(--divider-color);
      background: transparent;
      color: var(--primary-text-color);
    }

    .confirm-actions button:hover {
      background: rgba(var(--rgb-primary-color, 3, 169, 244), 0.08);
    }

    .confirm-actions .delete-action {
      background: var(--error-color, #f44336);
      color: #fff;
      border-color: var(--error-color, #f44336);
    }

    .confirm-actions .delete-action:hover {
      opacity: 0.9;
      background: var(--error-color, #f44336);
    }

    .confirm-actions .delete-action:disabled {
      opacity: 0.6;
      cursor: not-allowed;
    }

    .table-wrapper {
      overflow-x: auto;
    }

    @media (max-width: 768px) {
      .col-node,
      .col-ip,
      .col-owner {
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

    return html`
      ${this._data.clusters.map((c) => this._renderCluster(c))}
      ${this._deleteConfirm ? this._renderDeleteDialog() : nothing}
    `;
  }

  private _renderCluster(cluster: ClusterPods) {
    const filtered = this._getFilteredPods(cluster.pods);
    const namespaces = this._getNamespaces(cluster.pods);
    const phases = [...new Set(cluster.pods.map((p) => p.phase))].sort();

    return html`
      <div class="cluster-section">
        ${this._data!.clusters.length > 1
          ? html`<div class="cluster-name">${cluster.cluster_name}</div>`
          : nothing}

        <div class="filters">
          <input
            class="search-input"
            type="text"
            placeholder="Search pods..."
            .value=${this._searchQuery}
            @input=${(e: Event) => {
              this._searchQuery = (e.target as HTMLInputElement).value;
            }}
          />

          <select
            class="ns-select"
            .value=${this._namespaceFilter}
            @change=${(e: Event) => {
              this._namespaceFilter = (e.target as HTMLSelectElement).value;
            }}
          >
            <option value="all">All namespaces</option>
            ${namespaces.map((ns) => html`<option value=${ns}>${ns}</option>`)}
          </select>

          <button
            class="filter-chip"
            ?active=${this._phaseFilter === "all"}
            @click=${() => {
              this._phaseFilter = "all";
            }}
          >
            All
          </button>
          ${phases.map(
            (phase) => html`
              <button
                class="filter-chip"
                ?active=${this._phaseFilter === phase}
                @click=${() => {
                  this._phaseFilter = phase;
                }}
              >
                ${phase}
              </button>
            `,
          )}
        </div>

        <div class="pod-count">${filtered.length}/${cluster.pods.length} pods</div>

        ${filtered.length === 0
          ? html`<div class="empty">No pods match your filters.</div>`
          : html`
              <ha-card>
                <div class="table-wrapper">
                  <table class="pods-table">
                    <thead>
                      <tr>
                        <th @click=${() => this._handleSort("namespace")}>
                          Namespace
                          ${this._sortIcon("namespace")
                            ? html`<ha-icon
                                icon=${this._sortIcon("namespace")}
                              ></ha-icon>`
                            : nothing}
                        </th>
                        <th @click=${() => this._handleSort("name")}>
                          Name
                          ${this._sortIcon("name")
                            ? html`<ha-icon icon=${this._sortIcon("name")}></ha-icon>`
                            : nothing}
                        </th>
                        <th @click=${() => this._handleSort("phase")}>
                          Phase
                          ${this._sortIcon("phase")
                            ? html`<ha-icon icon=${this._sortIcon("phase")}></ha-icon>`
                            : nothing}
                        </th>
                        <th>Ready</th>
                        <th @click=${() => this._handleSort("restarts")}>
                          Restarts
                          ${this._sortIcon("restarts")
                            ? html`<ha-icon
                                icon=${this._sortIcon("restarts")}
                              ></ha-icon>`
                            : nothing}
                        </th>
                        <th
                          class="col-node"
                          @click=${() => this._handleSort("node_name")}
                        >
                          Node
                          ${this._sortIcon("node_name")
                            ? html`<ha-icon
                                icon=${this._sortIcon("node_name")}
                              ></ha-icon>`
                            : nothing}
                        </th>
                        <th class="col-ip">IP</th>
                        <th class="col-owner">Owner</th>
                        <th @click=${() => this._handleSort("age")}>
                          Age
                          ${this._sortIcon("age")
                            ? html`<ha-icon icon=${this._sortIcon("age")}></ha-icon>`
                            : nothing}
                        </th>
                        <th class="col-actions"></th>
                      </tr>
                    </thead>
                    <tbody>
                      ${filtered.map((pod) =>
                        this._renderPodRow(cluster.entry_id, pod),
                      )}
                    </tbody>
                  </table>
                </div>
              </ha-card>
            `}
      </div>
    `;
  }

  private _renderPodRow(entryId: string, pod: PodData) {
    const phaseClass = PHASE_CLASSES[pod.phase] || "badge-unknown";

    return html`
      <tr>
        <td>${pod.namespace}</td>
        <td class="pod-name">${pod.name}</td>
        <td><span class="badge ${phaseClass}">${pod.phase}</span></td>
        <td>${pod.ready_containers}/${pod.total_containers}</td>
        <td class=${pod.restart_count > 5 ? "restart-warn" : ""}>
          ${pod.restart_count}
        </td>
        <td class="col-node">${pod.node_name}</td>
        <td class="col-ip mono">${pod.pod_ip}</td>
        <td class="col-owner">
          ${pod.owner_kind !== "N/A"
            ? html`<span class="owner-info">${pod.owner_kind}/${pod.owner_name}</span>`
            : html`<span class="owner-info">-</span>`}
        </td>
        <td>${this._formatAge(pod.creation_timestamp)}</td>
        <td>
          <button
            class="delete-btn"
            title="Delete pod"
            @click=${() => this._requestDelete(entryId, pod)}
          >
            <ha-icon icon="mdi:delete-outline"></ha-icon>
          </button>
        </td>
      </tr>
    `;
  }

  private _renderDeleteDialog() {
    const confirm = this._deleteConfirm!;
    return html`
      <div
        class="confirm-overlay"
        @click=${this._deleting ? nothing : this._cancelDelete}
      >
        <div class="confirm-dialog" @click=${(e: Event) => e.stopPropagation()}>
          <h3>Delete Pod</h3>
          <p>
            Are you sure you want to delete
            <span class="pod-ref">${confirm.namespace}/${confirm.pod_name}</span>? This
            action cannot be undone.
          </p>
          <div class="confirm-actions">
            <button @click=${this._cancelDelete} ?disabled=${this._deleting}>
              Cancel
            </button>
            <button
              class="delete-action"
              @click=${this._confirmDelete}
              ?disabled=${this._deleting}
            >
              ${this._deleting ? "Deleting..." : "Delete"}
            </button>
          </div>
        </div>
      </div>
    `;
  }
}
