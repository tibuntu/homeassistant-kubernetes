import { html, css, nothing } from "lit";
import { customElement, state } from "lit/decorators.js";
import { actionStyles } from "../styles/actions";
import { K8sDataView } from "./base-view";
import { stateStyles, filterStyles, badgeStyles, dialogStyles } from "../styles/shared";
import { formatAge, errorMessage } from "../utils/format";

/** Shape shared by Deployments and StatefulSets; they differ only in which
 * field reports ready replicas (see `REPLICA_KIND_META`). */
interface ReplicaWorkloadData {
  name: string;
  namespace: string;
  replicas: number;
  available_replicas: number;
  ready_replicas: number;
}

type DeploymentData = ReplicaWorkloadData;
type StatefulSetData = ReplicaWorkloadData;

interface DaemonSetData {
  name: string;
  namespace: string;
  desired_number_scheduled: number;
  number_available: number;
}

interface CronJobData {
  name: string;
  namespace: string;
  schedule: string;
  suspend: boolean;
  last_schedule_time: string | null;
  active_jobs_count: number;
}

interface JobData {
  name: string;
  namespace: string;
  completions: number;
  succeeded: number;
  failed: number;
  active: number;
  start_time: string | null;
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
  "all" | "deployments" | "statefulsets" | "daemonsets" | "cronjobs" | "jobs";
type WorkloadStatus = "healthy" | "degraded" | "stopped";
type StatusFilter = "all" | WorkloadStatus;

const STATUS_META: Record<WorkloadStatus, { badgeClass: string; label: string }> = {
  healthy: { badgeClass: "badge-healthy", label: "Healthy" },
  degraded: { badgeClass: "badge-degraded", label: "Degraded" },
  stopped: { badgeClass: "badge-stopped", label: "Stopped" },
};

type ReplicaKind = "deployment" | "statefulset";

const REPLICA_KIND_META: Record<
  ReplicaKind,
  {
    category: Extract<WorkloadCategory, "deployments" | "statefulsets">;
    icon: string;
    label: string;
    emptyLabel: string;
    readyField: "available_replicas" | "ready_replicas";
    actionPrefix: string;
  }
> = {
  deployment: {
    category: "deployments",
    icon: "mdi:rocket-launch",
    label: "Deployments",
    emptyLabel: "deployments",
    readyField: "available_replicas",
    actionPrefix: "deploy_",
  },
  statefulset: {
    category: "statefulsets",
    icon: "mdi:database",
    label: "StatefulSets",
    emptyLabel: "statefulsets",
    readyField: "ready_replicas",
    actionPrefix: "sts_",
  },
};

@customElement("k8s-workloads")
export class K8sWorkloads extends K8sDataView<WorkloadsResponse> {
  @state() private _namespaceFilter: string = "all";
  @state() private _categoryFilter: WorkloadCategory = "all";
  @state() private _statusFilter: StatusFilter = "all";
  @state() private _searchQuery: string = "";
  @state() private _actionInProgress: Set<string> = new Set();
  @state() private _actionError: string | null = null;
  @state() private _jobDeleteConfirm: {
    entry_id: string;
    job_name: string;
    namespace: string;
  } | null = null;
  @state() private _deletingJob = false;
  @state() private _collapsedCategories: Set<string> = new Set();
  @state() private _scaleTarget: {
    entry_id: string;
    workload_name: string;
    namespace: string;
    current: number;
  } | null = null;
  @state() private _scaleValue: number = 0;
  @state() private _scaling = false;

  protected loadErrorFallback = "Failed to load workloads data";

  protected async fetchData(): Promise<void> {
    const result: WorkloadsResponse = await this.hass.callWS({
      type: "kubernetes/workloads/list",
    });
    this._data = result;
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

  private _toggleCategory(category: string): void {
    const updated = new Set(this._collapsedCategories);
    if (updated.has(category)) {
      updated.delete(category);
    } else {
      updated.add(category);
    }
    this._collapsedCategories = updated;
  }

  private _handleCategoryKeydown(e: KeyboardEvent, category: string): void {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      this._toggleCategory(category);
    }
  }

  private _matchesNamespace(namespace: string): boolean {
    return this._namespaceFilter === "all" || namespace === this._namespaceFilter;
  }

  private _matchesSearch(name: string): boolean {
    if (!this._searchQuery) return true;
    return name.toLowerCase().includes(this._searchQuery.toLowerCase());
  }

  /** `formatAge` with the visible " ago" suffix, omitted for the "N/A" case. */
  private _formatAgo(timestamp: string | null): string {
    const age = formatAge(timestamp);
    return age === "N/A" ? age : `${age} ago`;
  }

  /** Run an action with per-card busy state; failures land in the error banner. */
  private async _runAction(actionKey: string, run: () => Promise<void>): Promise<void> {
    const updated = new Set(this._actionInProgress);
    updated.add(actionKey);
    this._actionInProgress = updated;
    try {
      await run();
    } catch (err: unknown) {
      const message = errorMessage(err, "Action failed");
      this._actionError = `Action failed: ${message}`;
      console.error("[k8s-workloads] Action failed:", err);
    } finally {
      const done = new Set(this._actionInProgress);
      done.delete(actionKey);
      this._actionInProgress = done;
    }
  }

  private _callService(
    service: string,
    data: Record<string, any>,
    actionKey: string,
  ): Promise<void> {
    return this._runAction(actionKey, async () => {
      await this.hass.callService("kubernetes", service, data);
      // Reload data after action
      this._scheduleReload(2000);
    });
  }

  private _setCronJobSuspend(
    entryId: string,
    cj: CronJobData,
    suspend: boolean,
    actionKey: string,
  ): Promise<void> {
    return this._runAction(actionKey, async () => {
      await this.hass.callWS({
        type: "kubernetes/cronjobs/suspend",
        entry_id: entryId,
        cronjob_name: cj.name,
        namespace: cj.namespace,
        suspend,
      });
      // The backend refreshed the coordinator before answering.
      await this._loadData();
    });
  }

  static styles = [
    actionStyles,
    stateStyles,
    filterStyles,
    badgeStyles,
    dialogStyles,
    css`
      .cluster-section {
        margin-bottom: 24px;
      }

      .cluster-name {
        font-size: 20px;
        font-weight: 500;
        color: var(--primary-text-color);
        margin-bottom: 12px;
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
        cursor: pointer;
        user-select: none;
      }

      .category-header:hover {
        color: var(--primary-color);
      }

      .category-chevron {
        --mdc-icon-size: 18px;
        transition: transform 0.2s;
        margin-left: auto;
      }

      .category-chevron[data-collapsed] {
        transform: rotate(-90deg);
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

      .replica-info {
        font-size: 13px;
        color: var(--secondary-text-color);
        white-space: nowrap;
      }

      .replica-info.scalable {
        cursor: pointer;
        border-radius: 4px;
        padding: 2px 6px;
        transition: background 0.2s;
      }

      .replica-info.scalable:hover,
      .replica-info.scalable:focus {
        background: rgba(var(--rgb-primary-color, 3, 169, 244), 0.1);
        color: var(--primary-color);
        outline: none;
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

      .last-schedule {
        font-size: 12px;
        color: var(--secondary-text-color);
      }

      .scale-controls {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 12px;
        margin-bottom: 20px;
      }

      .scale-btn {
        display: flex;
        align-items: center;
        justify-content: center;
        width: 36px;
        height: 36px;
        border-radius: 50%;
        border: 1px solid var(--divider-color);
        background: transparent;
        color: var(--primary-text-color);
        cursor: pointer;
        --mdc-icon-size: 18px;
      }

      .scale-btn:hover:not(:disabled) {
        background: rgba(var(--rgb-primary-color, 3, 169, 244), 0.1);
        border-color: var(--primary-color);
        color: var(--primary-color);
      }

      .scale-btn:disabled {
        opacity: 0.4;
        cursor: not-allowed;
      }

      .scale-input {
        width: 64px;
        text-align: center;
        font-size: 20px;
        font-weight: 500;
        padding: 6px;
        border: 1px solid var(--divider-color);
        border-radius: 8px;
        background: var(--card-background-color, var(--primary-background-color));
        color: var(--primary-text-color);
      }

      .scale-input:focus {
        outline: none;
        border-color: var(--primary-color);
      }

      .confirm-actions .scale-action {
        background: var(--primary-color);
        color: var(--text-primary-color, #fff);
        border-color: var(--primary-color);
      }

      .confirm-actions .scale-action:hover:not(:disabled) {
        opacity: 0.9;
      }

      .confirm-actions .scale-action:disabled {
        opacity: 0.6;
        cursor: not-allowed;
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
    `,
  ];

  protected render() {
    const state = this.renderState(!this._data?.clusters.length);
    if (state !== nothing) return state;

    return html`
      ${
        this._actionError
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
          : nothing
      }
      ${this._data!.clusters.map((c) => this._renderCluster(c))}
      ${this._jobDeleteConfirm ? this._renderJobDeleteDialog() : nothing}
      ${this._scaleTarget ? this._renderScaleDialog() : nothing}
    `;
  }

  private _renderCluster(cluster: ClusterWorkloads) {
    const namespaces = this._getNamespaces(cluster);

    return html`
      <div class="cluster-section">
        ${
          this._data!.clusters.length > 1
            ? html`<div class="cluster-name">${cluster.cluster_name}</div>`
            : nothing
        }

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

        ${
          this._shouldShowCategory("deployments")
            ? this._renderReplicaCategory(
                "deployment",
                cluster.deployments,
                cluster.entry_id,
              )
            : nothing
        }
        ${
          this._shouldShowCategory("statefulsets")
            ? this._renderReplicaCategory(
                "statefulset",
                cluster.statefulsets,
                cluster.entry_id,
              )
            : nothing
        }
        ${
          this._shouldShowCategory("daemonsets")
            ? this._renderDaemonSets(cluster.daemonsets, cluster.entry_id)
            : nothing
        }
        ${
          this._shouldShowCategory("cronjobs")
            ? this._renderCronJobs(cluster.cronjobs, cluster.entry_id)
            : nothing
        }
        ${this._shouldShowCategory("jobs") ? this._renderJobs(cluster.entry_id, cluster.jobs) : nothing}
      </div>
    `;
  }

  private _shouldShowCategory(category: WorkloadCategory): boolean {
    return this._categoryFilter === "all" || this._categoryFilter === category;
  }

  private _getReplicaStatus(
    item: ReplicaWorkloadData,
    kind: ReplicaKind,
  ): WorkloadStatus {
    if (item.replicas === 0) return "stopped";
    const ready = item[REPLICA_KIND_META[kind].readyField] || 0;
    if (ready < item.replicas) return "degraded";
    return "healthy";
  }

  private _getDaemonSetStatus(ds: DaemonSetData): WorkloadStatus {
    if (ds.desired_number_scheduled === 0) return "stopped";
    if ((ds.number_available || 0) < ds.desired_number_scheduled) return "degraded";
    return "healthy";
  }

  private _matchesStatusFilter(status: WorkloadStatus): boolean {
    return this._statusFilter === "all" || this._statusFilter === status;
  }

  private _renderReplicaCategory(
    kind: ReplicaKind,
    items: ReplicaWorkloadData[],
    entryId: string,
  ) {
    const meta = REPLICA_KIND_META[kind];
    const filtered = items.filter(
      (item) =>
        this._matchesNamespace(item.namespace) &&
        this._matchesSearch(item.name) &&
        this._matchesStatusFilter(this._getReplicaStatus(item, kind)),
    );

    if (filtered.length === 0 && this._categoryFilter !== "all") {
      return html`<div class="empty">No ${meta.emptyLabel} match your filters.</div>`;
    }
    if (filtered.length === 0) return nothing;

    return html`
      <div class="category-section">
        <div
          class="category-header"
          role="button"
          tabindex="0"
          @click=${() => this._toggleCategory(meta.category)}
          @keydown=${(e: KeyboardEvent) => this._handleCategoryKeydown(e, meta.category)}
        >
          <ha-icon icon=${meta.icon}></ha-icon>
          ${meta.label}
          <span class="category-count">(${filtered.length})</span>
          <ha-icon
            class="category-chevron"
            icon="mdi:chevron-down"
            ?data-collapsed=${this._collapsedCategories.has(meta.category)}
          ></ha-icon>
        </div>
        ${
          this._collapsedCategories.has(meta.category)
            ? nothing
            : filtered.map((item) => this._renderReplicaCard(kind, item, entryId))
        }
      </div>
    `;
  }

  private _renderReplicaCard(
    kind: ReplicaKind,
    item: ReplicaWorkloadData,
    entryId: string,
  ) {
    const meta = REPLICA_KIND_META[kind];
    const status = this._getReplicaStatus(item, kind);
    const actionKey = `${meta.actionPrefix}${item.namespace}_${item.name}`;
    const busy = this._actionInProgress.has(actionKey);
    const ready = item[meta.readyField] ?? 0;

    return html`
      <ha-card class="workload-card">
        <div class="workload-row">
          <div class="workload-info">
            <div class="workload-name">${item.name}</div>
            <div class="workload-namespace">${item.namespace}</div>
          </div>
          <span
            class="replica-info scalable"
            role="button"
            tabindex="0"
            title="Click to scale"
            @click=${() =>
              this._openScaleDialog(entryId, item.name, item.namespace, item.replicas)}
            @keydown=${(e: KeyboardEvent) => {
              if (e.key === "Enter" || e.key === " ") {
                e.preventDefault();
                this._openScaleDialog(
                  entryId,
                  item.name,
                  item.namespace,
                  item.replicas,
                );
              }
            }}
          >
            ${ready}/${item.replicas} ready
          </span>
          <span class="badge ${STATUS_META[status].badgeClass}">
            ${STATUS_META[status].label}
          </span>
          <div class="workload-actions">
            ${
              item.replicas === 0
                ? html`
                    <button
                      class="action-btn start"
                      title="Start (scale to 1)"
                      ?disabled=${busy}
                      @click=${() =>
                        this._callService(
                          "start_workload",
                          {
                            workload_name: item.name,
                            namespace: item.namespace,
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
                            workload_name: item.name,
                            namespace: item.namespace,
                            entry_id: entryId,
                          },
                          actionKey,
                        )}
                    >
                      <ha-icon icon="mdi:stop"></ha-icon>
                    </button>
                  `
            }
            <button
              class="action-btn restart"
              title="Rolling restart"
              ?disabled=${busy}
              @click=${() =>
                this._callService(
                  "restart_workload",
                  {
                    workload_name: item.name,
                    namespace: item.namespace,
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
        <div
          class="category-header"
          role="button"
          tabindex="0"
          @click=${() => this._toggleCategory("daemonsets")}
          @keydown=${(e: KeyboardEvent) => this._handleCategoryKeydown(e, "daemonsets")}
        >
          <ha-icon icon="mdi:lan"></ha-icon>
          DaemonSets
          <span class="category-count">(${filtered.length})</span>
          <ha-icon
            class="category-chevron"
            icon="mdi:chevron-down"
            ?data-collapsed=${this._collapsedCategories.has("daemonsets")}
          ></ha-icon>
        </div>
        ${this._collapsedCategories.has("daemonsets") ? nothing : filtered.map((ds) => this._renderDaemonSetCard(ds, entryId))}
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
          <span class="badge ${STATUS_META[status].badgeClass}">
            ${STATUS_META[status].label}
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
        <div
          class="category-header"
          role="button"
          tabindex="0"
          @click=${() => this._toggleCategory("cronjobs")}
          @keydown=${(e: KeyboardEvent) => this._handleCategoryKeydown(e, "cronjobs")}
        >
          <ha-icon icon="mdi:clock-outline"></ha-icon>
          CronJobs
          <span class="category-count">(${statusFiltered.length})</span>
          <ha-icon
            class="category-chevron"
            icon="mdi:chevron-down"
            ?data-collapsed=${this._collapsedCategories.has("cronjobs")}
          ></ha-icon>
        </div>
        ${this._collapsedCategories.has("cronjobs") ? nothing : statusFiltered.map((cj) => this._renderCronJobCard(cj, entryId))}
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
          ${
            cj.active_jobs_count > 0
              ? html`<span class="badge badge-active"
                  >${cj.active_jobs_count} active</span
                >`
              : nothing
          }
          ${
            cj.suspend
              ? html`<span class="badge badge-suspended">Suspended</span>`
              : html`<span class="badge badge-healthy">Active</span>`
          }
          ${
            cj.last_schedule_time
              ? html`<span class="last-schedule"
                  >Last: ${this._formatAgo(cj.last_schedule_time)}</span
                >`
              : nothing
          }
          <div class="workload-actions">
            <button
              class="action-btn ${cj.suspend ? "start" : "suspend"}"
              title=${cj.suspend ? "Resume schedule" : "Suspend schedule"}
              ?disabled=${busy}
              @click=${() =>
                this._setCronJobSuspend(entryId, cj, !cj.suspend, actionKey)}
            >
              <ha-icon
                icon=${cj.suspend ? "mdi:play-circle-outline" : "mdi:pause-circle-outline"}
              ></ha-icon>
            </button>
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

  private _renderJobs(entryId: string, jobs: JobData[]) {
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
        <div
          class="category-header"
          role="button"
          tabindex="0"
          @click=${() => this._toggleCategory("jobs")}
          @keydown=${(e: KeyboardEvent) => this._handleCategoryKeydown(e, "jobs")}
        >
          <ha-icon icon="mdi:briefcase-check"></ha-icon>
          Jobs
          <span class="category-count">(${statusFiltered.length})</span>
          <ha-icon
            class="category-chevron"
            icon="mdi:chevron-down"
            ?data-collapsed=${this._collapsedCategories.has("jobs")}
          ></ha-icon>
        </div>
        ${this._collapsedCategories.has("jobs") ? nothing : statusFiltered.map((j) => this._renderJobCard(entryId, j))}
      </div>
    `;
  }

  private _renderJobCard(entryId: string, j: JobData) {
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
          ${
            j.active > 0
              ? html`<span class="badge badge-active">${j.active} active</span>`
              : nothing
          }
          ${
            hasFailed
              ? html`<span class="badge badge-failed">${j.failed} failed</span>`
              : nothing
          }
          ${
            isComplete
              ? html`<span class="badge badge-complete">Complete</span>`
              : nothing
          }
          ${
            j.start_time
              ? html`<span class="last-schedule"
                  >Started: ${this._formatAgo(j.start_time)}</span
                >`
              : nothing
          }
          <div class="workload-actions">
            <button
              class="action-btn delete"
              title="Delete Job"
              ?disabled=${this._deletingJob}
              @click=${() => this._requestJobDelete(entryId, j)}
            >
              <ha-icon icon="mdi:delete-outline"></ha-icon>
            </button>
          </div>
        </div>
      </ha-card>
    `;
  }

  private _openScaleDialog(
    entryId: string,
    name: string,
    namespace: string,
    current: number,
  ): void {
    this._scaleTarget = {
      entry_id: entryId,
      workload_name: name,
      namespace,
      current,
    };
    this._scaleValue = current;
  }

  private _cancelScale(): void {
    this._scaleTarget = null;
  }

  private async _confirmScale(): Promise<void> {
    if (!this._scaleTarget) return;
    this._scaling = true;
    try {
      await this.hass.callService("kubernetes", "scale_workload", {
        workload_name: this._scaleTarget.workload_name,
        namespace: this._scaleTarget.namespace,
        entry_id: this._scaleTarget.entry_id,
        replicas: this._scaleValue,
      });
      this._scaleTarget = null;
      this._scheduleReload(2000);
    } catch (err: unknown) {
      this._actionError = errorMessage(err, "Failed to scale workload");
      this._scaleTarget = null;
    } finally {
      this._scaling = false;
    }
  }

  private _renderScaleDialog() {
    const target = this._scaleTarget!;
    return html`
      <div
        class="confirm-overlay"
        tabindex="-1"
        autofocus
        @click=${this._scaling ? nothing : this._cancelScale}
        @keydown=${this._onOverlayKeydown(this._scaling ? nothing : this._cancelScale)}
      >
        <div class="confirm-dialog" @click=${(e: Event) => e.stopPropagation()}>
          <h3>Scale Workload</h3>
          <p>
            <span class="confirm-ref">${target.namespace}/${target.workload_name}</span>
          </p>
          <div class="scale-controls">
            <button
              class="scale-btn"
              ?disabled=${this._scaleValue <= 0 || this._scaling}
              @click=${() => this._scaleValue--}
            >
              <ha-icon icon="mdi:minus"></ha-icon>
            </button>
            <input
              class="scale-input"
              type="number"
              min="0"
              .value=${String(this._scaleValue)}
              ?disabled=${this._scaling}
              @input=${(e: InputEvent) => {
                const v = parseInt((e.target as HTMLInputElement).value, 10);
                if (!isNaN(v) && v >= 0) this._scaleValue = v;
              }}
            />
            <button
              class="scale-btn"
              ?disabled=${this._scaling}
              @click=${() => this._scaleValue++}
            >
              <ha-icon icon="mdi:plus"></ha-icon>
            </button>
          </div>
          <div class="confirm-actions">
            <button @click=${this._cancelScale} ?disabled=${this._scaling}>
              Cancel
            </button>
            <button
              class="scale-action"
              @click=${this._confirmScale}
              ?disabled=${this._scaling || this._scaleValue === target.current}
            >
              ${this._scaling ? "Scaling..." : "Scale"}
            </button>
          </div>
        </div>
      </div>
    `;
  }

  private _requestJobDelete(entryId: string, j: JobData): void {
    this._jobDeleteConfirm = {
      entry_id: entryId,
      job_name: j.name,
      namespace: j.namespace,
    };
  }

  private _cancelJobDelete(): void {
    this._jobDeleteConfirm = null;
  }

  private async _confirmJobDelete(): Promise<void> {
    if (!this._jobDeleteConfirm) return;
    this._deletingJob = true;
    try {
      await this.hass.callWS({
        type: "kubernetes/jobs/delete",
        entry_id: this._jobDeleteConfirm.entry_id,
        job_name: this._jobDeleteConfirm.job_name,
        namespace: this._jobDeleteConfirm.namespace,
      });
      this._jobDeleteConfirm = null;
      await this._loadData();
    } catch (err: unknown) {
      this._actionError = errorMessage(err, "Failed to delete job");
      this._jobDeleteConfirm = null;
    } finally {
      this._deletingJob = false;
    }
  }

  private _renderJobDeleteDialog() {
    const confirm = this._jobDeleteConfirm!;
    return html`
      <div
        class="confirm-overlay"
        tabindex="-1"
        autofocus
        @click=${this._deletingJob ? nothing : this._cancelJobDelete}
        @keydown=${this._onOverlayKeydown(this._deletingJob ? nothing : this._cancelJobDelete)}
      >
        <div class="confirm-dialog" @click=${(e: Event) => e.stopPropagation()}>
          <h3>Delete Job</h3>
          <p>
            Are you sure you want to delete
            <span class="confirm-ref">${confirm.namespace}/${confirm.job_name}</span>?
            This action cannot be undone.
          </p>
          <div class="confirm-actions">
            <button @click=${this._cancelJobDelete} ?disabled=${this._deletingJob}>
              Cancel
            </button>
            <button
              class="delete-action"
              @click=${this._confirmJobDelete}
              ?disabled=${this._deletingJob}
            >
              ${this._deletingJob ? "Deleting..." : "Delete"}
            </button>
          </div>
        </div>
      </div>
    `;
  }
}
