import { LitElement, html, css, nothing, PropertyValues } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import type { HomeAssistant } from "../types/homeassistant";

interface DeploymentData {
  name: string;
  namespace: string;
  replicas: number;
  available_replicas: number;
  ready_replicas: number;
  is_running: boolean;
}

interface StatefulSetData {
  name: string;
  namespace: string;
  replicas: number;
  available_replicas: number;
  ready_replicas: number;
  is_running: boolean;
}

interface DaemonSetData {
  name: string;
  namespace: string;
  desired_number_scheduled: number;
  current_number_scheduled: number;
  number_ready: number;
  number_available: number;
  is_running: boolean;
}

interface CronJobData {
  name: string;
  namespace: string;
  schedule: string;
  suspend: boolean;
  last_schedule_time: string | null;
  active_jobs_count: number;
  concurrency_policy: string;
}

interface JobData {
  name: string;
  namespace: string;
  completions: number;
  succeeded: number;
  failed: number;
  active: number;
  start_time: string | null;
  completion_time: string | null;
}

interface ClusterWorkloads {
  entry_id: string;
  cluster_name: string;
  deployments: DeploymentData[];
  statefulsets: StatefulSetData[];
  daemonsets: DaemonSetData[];
  cronjobs: CronJobData[];
  jobs: JobData[];
}

interface WorkloadsResponse {
  clusters: ClusterWorkloads[];
}

type WorkloadCategory =
  | "all"
  | "deployments"
  | "statefulsets"
  | "daemonsets"
  | "cronjobs"
  | "jobs";
type StatusFilter = "all" | "healthy" | "degraded" | "stopped";

@customElement("k8s-workloads")
export class K8sWorkloads extends LitElement {
  @property({ attribute: false }) public hass!: HomeAssistant;

  @state() private _data: WorkloadsResponse | null = null;
  @state() private _loading = true;
  @state() private _error: string | null = null;
  @state() private _namespaceFilter: string = "all";
  @state() private _categoryFilter: WorkloadCategory = "all";
  @state() private _statusFilter: StatusFilter = "all";
  @state() private _searchQuery: string = "";
  @state() private _actionInProgress: Set<string> = new Set();
  @state() private _actionError: string | null = null;

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
      const result: WorkloadsResponse = await this.hass.callWS({
        type: "kubernetes/workloads/list",
      });
      this._data = result;
    } catch (err: any) {
      this._error = err.message || "Failed to load workloads data";
    } finally {
      this._loading = false;
      this._loadingInFlight = false;
    }
  }

  private _getNamespaces(cluster: ClusterWorkloads): string[] {
    const namespaces = new Set<string>();
    for (const d of cluster.deployments) namespaces.add(d.namespace);
    for (const s of cluster.statefulsets) namespaces.add(s.namespace);
    for (const ds of cluster.daemonsets) namespaces.add(ds.namespace);
    for (const cj of cluster.cronjobs) namespaces.add(cj.namespace);
    for (const j of cluster.jobs) namespaces.add(j.namespace);
    return [...namespaces].sort();
  }

  private _matchesNamespace(namespace: string): boolean {
    return this._namespaceFilter === "all" || namespace === this._namespaceFilter;
  }

  private _matchesSearch(name: string): boolean {
    if (!this._searchQuery) return true;
    return name.toLowerCase().includes(this._searchQuery.toLowerCase());
  }

  private _formatAge(timestamp: string | null): string {
    if (!timestamp) return "N/A";
    const created = new Date(timestamp).getTime();
    const now = Date.now();
    const diff = Math.max(0, Math.floor((now - created) / 1000));
    if (diff < 60) return `${diff}s ago`;
    if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
    if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
    return `${Math.floor(diff / 86400)}d ago`;
  }

  private async _callService(
    service: string,
    data: Record<string, any>,
    actionKey: string,
  ): Promise<void> {
    const updated = new Set(this._actionInProgress);
    updated.add(actionKey);
    this._actionInProgress = updated;
    try {
      await this.hass.callService("kubernetes", service, data);
      // Reload data after action
      setTimeout(() => this._loadData(), 2000);
    } catch (err: any) {
      const message = err?.message || "Service call failed";
      this._actionError = `Action failed: ${message}`;
      console.error("[k8s-workloads] Service call failed:", err);
    } finally {
      const done = new Set(this._actionInProgress);
      done.delete(actionKey);
      this._actionInProgress = done;
    }
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

    select.filter-select {
      padding: 6px 12px;
      border: 1px solid var(--divider-color);
      border-radius: 8px;
      background: var(--card-background-color, var(--primary-background-color));
      color: var(--primary-text-color);
      font-size: 13px;
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

    .category-section {
      margin-bottom: 20px;
    }

    .category-header {
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 8px 0;
      font-size: 16px;
      font-weight: 500;
      color: var(--primary-text-color);
      --mdc-icon-size: 20px;
    }

    .category-count {
      font-size: 13px;
      color: var(--secondary-text-color);
      font-weight: 400;
    }

    .workload-card {
      margin-bottom: 8px;
      border-radius: 12px;
      overflow: hidden;
    }

    .workload-row {
      display: flex;
      align-items: center;
      gap: 16px;
      padding: 12px 16px;
      font-size: 14px;
    }

    .workload-info {
      flex: 1;
      min-width: 0;
    }

    .workload-name {
      font-weight: 500;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }

    .workload-namespace {
      font-size: 12px;
      color: var(--secondary-text-color);
    }

    .workload-status {
      display: flex;
      align-items: center;
      gap: 8px;
      flex-shrink: 0;
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

    .badge-healthy {
      background: rgba(var(--rgb-success-color, 76, 175, 80), 0.15);
      color: var(--success-color, #4caf50);
    }

    .badge-degraded {
      background: rgba(var(--rgb-warning-color, 255, 152, 0), 0.15);
      color: var(--warning-color, #ff9800);
    }

    .badge-stopped {
      background: rgba(var(--rgb-disabled-color, 158, 158, 158), 0.15);
      color: var(--disabled-color, #9e9e9e);
    }

    .badge-failed {
      background: rgba(var(--rgb-error-color, 244, 67, 54), 0.15);
      color: var(--error-color, #f44336);
    }

    .badge-active {
      background: rgba(var(--rgb-info-color, 33, 150, 243), 0.15);
      color: var(--info-color, #2196f3);
    }

    .badge-suspended {
      background: rgba(var(--rgb-disabled-color, 158, 158, 158), 0.15);
      color: var(--disabled-color, #9e9e9e);
    }

    .badge-complete {
      background: rgba(var(--rgb-success-color, 76, 175, 80), 0.15);
      color: var(--success-color, #4caf50);
    }

    .replica-info {
      font-size: 13px;
      color: var(--secondary-text-color);
      white-space: nowrap;
    }

    .schedule-info {
      font-size: 13px;
      color: var(--secondary-text-color);
      font-family: monospace;
    }

    .workload-actions {
      display: flex;
      gap: 4px;
      flex-shrink: 0;
    }

    .action-btn {
      display: flex;
      align-items: center;
      justify-content: center;
      width: 32px;
      height: 32px;
      border: none;
      border-radius: 50%;
      background: transparent;
      cursor: pointer;
      color: var(--secondary-text-color);
      --mdc-icon-size: 18px;
      transition:
        background 0.15s,
        color 0.15s;
    }

    .action-btn:hover {
      background: rgba(var(--rgb-primary-color, 3, 169, 244), 0.1);
      color: var(--primary-color);
    }

    .action-btn[disabled] {
      opacity: 0.4;
      cursor: not-allowed;
    }

    .action-btn.stop:hover {
      background: rgba(var(--rgb-error-color, 244, 67, 54), 0.1);
      color: var(--error-color, #f44336);
    }

    .action-btn.start:hover {
      background: rgba(var(--rgb-success-color, 76, 175, 80), 0.1);
      color: var(--success-color, #4caf50);
    }

    .action-btn.restart:hover {
      background: rgba(var(--rgb-warning-color, 255, 152, 0), 0.1);
      color: var(--warning-color, #ff9800);
    }

    .last-schedule {
      font-size: 12px;
      color: var(--secondary-text-color);
    }

    .action-error {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      padding: 10px 16px;
      margin-bottom: 16px;
      border-radius: 8px;
      background: rgba(var(--rgb-error-color, 244, 67, 54), 0.1);
      color: var(--error-color, #f44336);
      font-size: 14px;
    }

    .action-error .dismiss-btn {
      display: flex;
      align-items: center;
      justify-content: center;
      width: 24px;
      height: 24px;
      border: none;
      border-radius: 50%;
      background: transparent;
      cursor: pointer;
      color: var(--error-color, #f44336);
      --mdc-icon-size: 16px;
      flex-shrink: 0;
    }

    .action-error .dismiss-btn:hover {
      background: rgba(var(--rgb-error-color, 244, 67, 54), 0.15);
    }

    @media (max-width: 768px) {
      .workload-row {
        flex-wrap: wrap;
        gap: 8px;
      }

      .replica-info,
      .schedule-info {
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
      ${this._actionError
        ? html`
            <div class="action-error">
              <span>${this._actionError}</span>
              <button
                class="dismiss-btn"
                @click=${() => {
                  this._actionError = null;
                }}
                title="Dismiss"
              >
                <ha-icon icon="mdi:close"></ha-icon>
              </button>
            </div>
          `
        : nothing}
      ${this._data.clusters.map((c) => this._renderCluster(c))}
    `;
  }

  private _renderCluster(cluster: ClusterWorkloads) {
    const namespaces = this._getNamespaces(cluster);

    return html`
      <div class="cluster-section">
        ${this._data!.clusters.length > 1
          ? html`<div class="cluster-name">${cluster.cluster_name}</div>`
          : nothing}

        <div class="filters">
          <input
            class="search-input"
            type="text"
            placeholder="Search workloads..."
            .value=${this._searchQuery}
            @input=${(e: Event) => {
              this._searchQuery = (e.target as HTMLInputElement).value;
            }}
          />

          <select
            class="filter-select"
            .value=${this._namespaceFilter}
            @change=${(e: Event) => {
              this._namespaceFilter = (e.target as HTMLSelectElement).value;
            }}
          >
            <option value="all">All namespaces</option>
            ${namespaces.map((ns) => html`<option value=${ns}>${ns}</option>`)}
          </select>

          <select
            class="filter-select"
            .value=${this._categoryFilter}
            @change=${(e: Event) => {
              this._categoryFilter = (e.target as HTMLSelectElement)
                .value as WorkloadCategory;
            }}
          >
            <option value="all">All types</option>
            <option value="deployments">Deployments</option>
            <option value="statefulsets">StatefulSets</option>
            <option value="daemonsets">DaemonSets</option>
            <option value="cronjobs">CronJobs</option>
            <option value="jobs">Jobs</option>
          </select>

          ${(["all", "healthy", "degraded", "stopped"] as StatusFilter[]).map(
            (f) => html`
              <button
                class="filter-chip"
                ?active=${this._statusFilter === f}
                @click=${() => {
                  this._statusFilter = f;
                }}
              >
                ${f.charAt(0).toUpperCase() + f.slice(1)}
              </button>
            `,
          )}
        </div>

        ${this._shouldShowCategory("deployments")
          ? this._renderDeployments(cluster.deployments, cluster.entry_id)
          : nothing}
        ${this._shouldShowCategory("statefulsets")
          ? this._renderStatefulSets(cluster.statefulsets, cluster.entry_id)
          : nothing}
        ${this._shouldShowCategory("daemonsets")
          ? this._renderDaemonSets(cluster.daemonsets, cluster.entry_id)
          : nothing}
        ${this._shouldShowCategory("cronjobs")
          ? this._renderCronJobs(cluster.cronjobs, cluster.entry_id)
          : nothing}
        ${this._shouldShowCategory("jobs") ? this._renderJobs(cluster.jobs) : nothing}
      </div>
    `;
  }

  private _shouldShowCategory(category: WorkloadCategory): boolean {
    return this._categoryFilter === "all" || this._categoryFilter === category;
  }

  private _getDeploymentStatus(d: DeploymentData): StatusFilter {
    if (d.replicas === 0) return "stopped";
    if ((d.available_replicas || 0) < d.replicas) return "degraded";
    return "healthy";
  }

  private _getStatefulSetStatus(s: StatefulSetData): StatusFilter {
    if (s.replicas === 0) return "stopped";
    if ((s.ready_replicas || 0) < s.replicas) return "degraded";
    return "healthy";
  }

  private _getDaemonSetStatus(ds: DaemonSetData): StatusFilter {
    if (ds.desired_number_scheduled === 0) return "stopped";
    if ((ds.number_available || 0) < ds.desired_number_scheduled) return "degraded";
    return "healthy";
  }

  private _matchesStatusFilter(status: StatusFilter): boolean {
    return this._statusFilter === "all" || this._statusFilter === status;
  }

  private _statusBadgeClass(status: StatusFilter): string {
    const map: Record<StatusFilter, string> = {
      all: "",
      healthy: "badge-healthy",
      degraded: "badge-degraded",
      stopped: "badge-stopped",
    };
    return map[status] || "";
  }

  private _statusLabel(status: StatusFilter): string {
    const map: Record<StatusFilter, string> = {
      all: "",
      healthy: "Healthy",
      degraded: "Degraded",
      stopped: "Stopped",
    };
    return map[status] || "";
  }

  private _renderDeployments(deployments: DeploymentData[], entryId: string) {
    const filtered = deployments.filter(
      (d) =>
        this._matchesNamespace(d.namespace) &&
        this._matchesSearch(d.name) &&
        this._matchesStatusFilter(this._getDeploymentStatus(d)),
    );

    if (filtered.length === 0 && this._categoryFilter !== "all") {
      return html`<div class="empty">No deployments match your filters.</div>`;
    }
    if (filtered.length === 0) return nothing;

    return html`
      <div class="category-section">
        <div class="category-header">
          <ha-icon icon="mdi:rocket-launch"></ha-icon>
          Deployments
          <span class="category-count">(${filtered.length})</span>
        </div>
        ${filtered.map((d) => this._renderDeploymentCard(d, entryId))}
      </div>
    `;
  }

  private _renderDeploymentCard(d: DeploymentData, entryId: string) {
    const status = this._getDeploymentStatus(d);
    const actionKey = `deploy_${d.namespace}_${d.name}`;
    const busy = this._actionInProgress.has(actionKey);

    return html`
      <ha-card class="workload-card">
        <div class="workload-row">
          <div class="workload-info">
            <div class="workload-name">${d.name}</div>
            <div class="workload-namespace">${d.namespace}</div>
          </div>
          <span class="replica-info">
            ${d.available_replicas ?? 0}/${d.replicas} ready
          </span>
          <span class="badge ${this._statusBadgeClass(status)}">
            ${this._statusLabel(status)}
          </span>
          <div class="workload-actions">
            ${d.replicas === 0
              ? html`
                  <button
                    class="action-btn start"
                    title="Start (scale to 1)"
                    ?disabled=${busy}
                    @click=${() =>
                      this._callService(
                        "start_workload",
                        {
                          workload_name: d.name,
                          namespace: d.namespace,
                          entry_id: entryId,
                        },
                        actionKey,
                      )}
                  >
                    <ha-icon icon="mdi:play"></ha-icon>
                  </button>
                `
              : html`
                  <button
                    class="action-btn stop"
                    title="Stop (scale to 0)"
                    ?disabled=${busy}
                    @click=${() =>
                      this._callService(
                        "stop_workload",
                        {
                          workload_name: d.name,
                          namespace: d.namespace,
                          entry_id: entryId,
                        },
                        actionKey,
                      )}
                  >
                    <ha-icon icon="mdi:stop"></ha-icon>
                  </button>
                `}
            <button
              class="action-btn restart"
              title="Rolling restart"
              ?disabled=${busy}
              @click=${() =>
                this._callService(
                  "restart_workload",
                  {
                    workload_name: d.name,
                    namespace: d.namespace,
                    entry_id: entryId,
                  },
                  actionKey,
                )}
            >
              <ha-icon icon="mdi:restart"></ha-icon>
            </button>
          </div>
        </div>
      </ha-card>
    `;
  }

  private _renderStatefulSets(statefulsets: StatefulSetData[], entryId: string) {
    const filtered = statefulsets.filter(
      (s) =>
        this._matchesNamespace(s.namespace) &&
        this._matchesSearch(s.name) &&
        this._matchesStatusFilter(this._getStatefulSetStatus(s)),
    );

    if (filtered.length === 0 && this._categoryFilter !== "all") {
      return html`<div class="empty">No statefulsets match your filters.</div>`;
    }
    if (filtered.length === 0) return nothing;

    return html`
      <div class="category-section">
        <div class="category-header">
          <ha-icon icon="mdi:database"></ha-icon>
          StatefulSets
          <span class="category-count">(${filtered.length})</span>
        </div>
        ${filtered.map((s) => this._renderStatefulSetCard(s, entryId))}
      </div>
    `;
  }

  private _renderStatefulSetCard(s: StatefulSetData, entryId: string) {
    const status = this._getStatefulSetStatus(s);
    const actionKey = `sts_${s.namespace}_${s.name}`;
    const busy = this._actionInProgress.has(actionKey);

    return html`
      <ha-card class="workload-card">
        <div class="workload-row">
          <div class="workload-info">
            <div class="workload-name">${s.name}</div>
            <div class="workload-namespace">${s.namespace}</div>
          </div>
          <span class="replica-info">
            ${s.ready_replicas ?? 0}/${s.replicas} ready
          </span>
          <span class="badge ${this._statusBadgeClass(status)}">
            ${this._statusLabel(status)}
          </span>
          <div class="workload-actions">
            ${s.replicas === 0
              ? html`
                  <button
                    class="action-btn start"
                    title="Start (scale to 1)"
                    ?disabled=${busy}
                    @click=${() =>
                      this._callService(
                        "start_workload",
                        {
                          workload_name: s.name,
                          namespace: s.namespace,
                          entry_id: entryId,
                        },
                        actionKey,
                      )}
                  >
                    <ha-icon icon="mdi:play"></ha-icon>
                  </button>
                `
              : html`
                  <button
                    class="action-btn stop"
                    title="Stop (scale to 0)"
                    ?disabled=${busy}
                    @click=${() =>
                      this._callService(
                        "stop_workload",
                        {
                          workload_name: s.name,
                          namespace: s.namespace,
                          entry_id: entryId,
                        },
                        actionKey,
                      )}
                  >
                    <ha-icon icon="mdi:stop"></ha-icon>
                  </button>
                `}
            <button
              class="action-btn restart"
              title="Rolling restart"
              ?disabled=${busy}
              @click=${() =>
                this._callService(
                  "restart_workload",
                  {
                    workload_name: s.name,
                    namespace: s.namespace,
                    entry_id: entryId,
                  },
                  actionKey,
                )}
            >
              <ha-icon icon="mdi:restart"></ha-icon>
            </button>
          </div>
        </div>
      </ha-card>
    `;
  }

  private _renderDaemonSets(daemonsets: DaemonSetData[], entryId: string) {
    const filtered = daemonsets.filter(
      (ds) =>
        this._matchesNamespace(ds.namespace) &&
        this._matchesSearch(ds.name) &&
        this._matchesStatusFilter(this._getDaemonSetStatus(ds)),
    );

    if (filtered.length === 0 && this._categoryFilter !== "all") {
      return html`<div class="empty">No daemonsets match your filters.</div>`;
    }
    if (filtered.length === 0) return nothing;

    return html`
      <div class="category-section">
        <div class="category-header">
          <ha-icon icon="mdi:lan"></ha-icon>
          DaemonSets
          <span class="category-count">(${filtered.length})</span>
        </div>
        ${filtered.map((ds) => this._renderDaemonSetCard(ds, entryId))}
      </div>
    `;
  }

  private _renderDaemonSetCard(ds: DaemonSetData, entryId: string) {
    const status = this._getDaemonSetStatus(ds);
    const actionKey = `ds_${ds.namespace}_${ds.name}`;
    const busy = this._actionInProgress.has(actionKey);

    return html`
      <ha-card class="workload-card">
        <div class="workload-row">
          <div class="workload-info">
            <div class="workload-name">${ds.name}</div>
            <div class="workload-namespace">${ds.namespace}</div>
          </div>
          <span class="replica-info">
            ${ds.number_available ?? 0}/${ds.desired_number_scheduled} available
          </span>
          <span class="badge ${this._statusBadgeClass(status)}">
            ${this._statusLabel(status)}
          </span>
          <div class="workload-actions">
            <button
              class="action-btn restart"
              title="Rolling restart"
              ?disabled=${busy}
              @click=${() =>
                this._callService(
                  "restart_workload",
                  {
                    workload_name: ds.name,
                    namespace: ds.namespace,
                    entry_id: entryId,
                  },
                  actionKey,
                )}
            >
              <ha-icon icon="mdi:restart"></ha-icon>
            </button>
          </div>
        </div>
      </ha-card>
    `;
  }

  private _renderCronJobs(cronjobs: CronJobData[], entryId: string) {
    const filtered = cronjobs.filter(
      (cj) => this._matchesNamespace(cj.namespace) && this._matchesSearch(cj.name),
    );

    // Apply status filter for cronjobs: suspended = stopped, active = healthy
    const statusFiltered =
      this._statusFilter === "all"
        ? filtered
        : filtered.filter((cj) => {
            if (this._statusFilter === "stopped") return cj.suspend;
            if (this._statusFilter === "healthy") return !cj.suspend;
            return false;
          });

    if (statusFiltered.length === 0 && this._categoryFilter !== "all") {
      return html`<div class="empty">No cronjobs match your filters.</div>`;
    }
    if (statusFiltered.length === 0) return nothing;

    return html`
      <div class="category-section">
        <div class="category-header">
          <ha-icon icon="mdi:clock-outline"></ha-icon>
          CronJobs
          <span class="category-count">(${statusFiltered.length})</span>
        </div>
        ${statusFiltered.map((cj) => this._renderCronJobCard(cj, entryId))}
      </div>
    `;
  }

  private _renderCronJobCard(cj: CronJobData, entryId: string) {
    const actionKey = `cj_${cj.namespace}_${cj.name}`;
    const busy = this._actionInProgress.has(actionKey);

    return html`
      <ha-card class="workload-card">
        <div class="workload-row">
          <div class="workload-info">
            <div class="workload-name">${cj.name}</div>
            <div class="workload-namespace">${cj.namespace}</div>
          </div>
          <span class="schedule-info">${cj.schedule}</span>
          ${cj.active_jobs_count > 0
            ? html`<span class="badge badge-active"
                >${cj.active_jobs_count} active</span
              >`
            : nothing}
          ${cj.suspend
            ? html`<span class="badge badge-suspended">Suspended</span>`
            : html`<span class="badge badge-healthy">Active</span>`}
          ${cj.last_schedule_time
            ? html`<span class="last-schedule"
                >Last: ${this._formatAge(cj.last_schedule_time)}</span
              >`
            : nothing}
          <div class="workload-actions">
            <button
              class="action-btn start"
              title="Trigger now"
              ?disabled=${busy}
              @click=${() =>
                this._callService(
                  "start_workload",
                  {
                    workload_name: cj.name,
                    namespace: cj.namespace,
                    entry_id: entryId,
                  },
                  actionKey,
                )}
            >
              <ha-icon icon="mdi:play"></ha-icon>
            </button>
          </div>
        </div>
      </ha-card>
    `;
  }

  private _renderJobs(jobs: JobData[]) {
    const filtered = jobs.filter(
      (j) => this._matchesNamespace(j.namespace) && this._matchesSearch(j.name),
    );

    // Apply status filter for jobs
    const statusFiltered =
      this._statusFilter === "all"
        ? filtered
        : filtered.filter((j) => {
            if (this._statusFilter === "healthy") return j.succeeded >= j.completions;
            if (this._statusFilter === "degraded")
              return j.failed > 0 && j.succeeded < j.completions;
            if (this._statusFilter === "stopped") return j.active === 0;
            return true;
          });

    if (statusFiltered.length === 0 && this._categoryFilter !== "all") {
      return html`<div class="empty">No jobs match your filters.</div>`;
    }
    if (statusFiltered.length === 0) return nothing;

    return html`
      <div class="category-section">
        <div class="category-header">
          <ha-icon icon="mdi:briefcase-check"></ha-icon>
          Jobs
          <span class="category-count">(${statusFiltered.length})</span>
        </div>
        ${statusFiltered.map((j) => this._renderJobCard(j))}
      </div>
    `;
  }

  private _renderJobCard(j: JobData) {
    const isComplete = j.succeeded >= j.completions;
    const hasFailed = j.failed > 0;

    return html`
      <ha-card class="workload-card">
        <div class="workload-row">
          <div class="workload-info">
            <div class="workload-name">${j.name}</div>
            <div class="workload-namespace">${j.namespace}</div>
          </div>
          <span class="replica-info"> ${j.succeeded}/${j.completions} completed </span>
          ${j.active > 0
            ? html`<span class="badge badge-active">${j.active} active</span>`
            : nothing}
          ${hasFailed
            ? html`<span class="badge badge-failed">${j.failed} failed</span>`
            : nothing}
          ${isComplete
            ? html`<span class="badge badge-complete">Complete</span>`
            : nothing}
          ${j.start_time
            ? html`<span class="last-schedule"
                >Started: ${this._formatAge(j.start_time)}</span
              >`
            : nothing}
        </div>
      </ha-card>
    `;
  }
}
