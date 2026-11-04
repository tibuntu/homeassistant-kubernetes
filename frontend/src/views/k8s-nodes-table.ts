import { html, css, nothing } from "lit";
import { customElement, state } from "lit/decorators.js";
import { actionStyles } from "../styles/actions";
import { K8sDataView } from "./base-view";
import { stateStyles, filterStyles, badgeStyles, dialogStyles } from "../styles/shared";
import {
  formatAge,
  toggleInSet,
  errorMessage,
  CONDITION_LABELS,
  isAdmin,
} from "../utils/format";

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

/** One node's entry in the `drain_node` service response. */
interface DrainResult {
  evicted: string[];
  skipped: { pod: string; reason: string }[];
  blocked: string[];
}

const SKIP_REASONS: Record<string, string> = {
  mirror_pod: "static pod",
  daemonset: "DaemonSet",
  completed: "finished",
  emptydir: "emptyDir data",
  unmanaged: "no controller",
  home_assistant: "Home Assistant itself",
};

@customElement("k8s-nodes-table")
export class K8sNodesTable extends K8sDataView<NodesResponse> {
  @state() private _expandedNodes: Set<string> = new Set();
  @state() private _statusFilter: string = "all";
  @state() private _searchQuery: string = "";
  @state() private _actionInProgress: Set<string> = new Set();
  @state() private _actionError: string | null = null;
  @state() private _drainTarget: { entry_id: string; node: string } | null = null;
  @state() private _drainOptions = {
    ignore_daemonsets: true,
    delete_emptydir_data: false,
    force: false,
    timeout: 120,
  };
  @state() private _draining = false;
  @state() private _drainResult: DrainResult | null = null;

  protected loadErrorFallback = "Failed to load nodes data";

  protected async fetchData(): Promise<void> {
    const result: NodesResponse = await this.hass.callWS({
      type: "kubernetes/nodes/list",
    });
    this._data = result;
  }

  private _toggleNode(nodeKey: string): void {
    this._expandedNodes = toggleInSet(this._expandedNodes, nodeKey);
  }

  private _getConditions(node: NodeData): string[] {
    const conditions: string[] = [];
    if (node.memory_pressure) conditions.push("memory_pressure");
    if (node.disk_pressure) conditions.push("disk_pressure");
    if (node.pid_pressure) conditions.push("pid_pressure");
    if (node.network_unavailable) conditions.push("network_unavailable");
    return conditions;
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

  /** Cordon (schedulable → false) or uncordon a node via the HA services. */
  private async _setSchedulable(
    entryId: string,
    node: NodeData,
    schedulable: boolean,
  ): Promise<void> {
    const actionKey = `${entryId}_${node.name}`;
    const updated = new Set(this._actionInProgress);
    updated.add(actionKey);
    this._actionInProgress = updated;
    try {
      await this.hass.callService(
        "kubernetes",
        schedulable ? "uncordon_node" : "cordon_node",
        { node_name: node.name, entry_id: entryId },
      );
      // The services request a coordinator refresh; reload now and let the
      // update push catch anything the cluster reports late.
      await this._loadData();
    } catch (err: unknown) {
      const message = errorMessage(err, "Action failed");
      this._actionError = `Action failed: ${message}`;
      console.error("[k8s-nodes-table] Action failed:", err);
    } finally {
      const done = new Set(this._actionInProgress);
      done.delete(actionKey);
      this._actionInProgress = done;
    }
  }

  private _requestDrain(entryId: string, node: NodeData): void {
    this._drainTarget = { entry_id: entryId, node: node.name };
    this._drainResult = null;
  }

  private _closeDrain(): void {
    this._drainTarget = null;
    this._drainResult = null;
  }

  /** Drain via the HA service; the dialog stays open to show its response. */
  private async _confirmDrain(): Promise<void> {
    if (!this._drainTarget) return;
    const { entry_id, node } = this._drainTarget;
    this._draining = true;
    try {
      const result = await this.hass.callService(
        "kubernetes",
        "drain_node",
        { node_name: node, entry_id, ...this._drainOptions },
        undefined,
        true,
        true,
      );
      const response = result?.response as Record<string, DrainResult> | undefined;
      this._drainResult = response?.[node] ?? { evicted: [], skipped: [], blocked: [] };
      await this._loadData();
    } catch (err: unknown) {
      this._actionError = `Drain failed: ${errorMessage(err, "Action failed")}`;
      this._drainTarget = null;
    } finally {
      this._draining = false;
    }
  }

  static styles = [
    actionStyles,
    stateStyles,
    filterStyles,
    badgeStyles,
    dialogStyles,
    css`
      .node-actions {
        display: flex;
        gap: 4px;
      }

      .drain-option {
        display: flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 12px;
        font-size: 14px;
        color: var(--primary-text-color);
      }

      .drain-option input[type="number"] {
        width: 80px;
        padding: 4px 8px;
        border: 1px solid var(--divider-color);
        border-radius: 4px;
        background: transparent;
        color: var(--primary-text-color);
      }

      .confirm-actions .drain-action {
        background: var(--warning-color, #ff9800);
        color: #fff;
        border-color: var(--warning-color, #ff9800);
      }

      .drain-section {
        margin-bottom: 12px;
        font-size: 14px;
        color: var(--primary-text-color);
      }

      .drain-section.blocked {
        color: var(--warning-color, #ff9800);
      }

      .drain-section ul {
        margin: 4px 0 0;
        padding-left: 20px;
        max-height: 120px;
        overflow-y: auto;
        font-family: monospace;
        font-size: 13px;
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
          grid-template-columns: 1fr auto auto;
          gap: 8px;
        }

        .node-ip,
        .node-resources,
        .node-age {
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
      ${this._drainTarget ? this._renderDrainDialog() : nothing}
    `;
  }

  private _renderDrainDialog() {
    const node = this._drainTarget!.node;
    const result = this._drainResult;
    const opts = this._drainOptions;
    return html`
      <div
        class="confirm-overlay"
        tabindex="-1"
        ${this._autofocusOverlay()}
        @click=${this._draining ? nothing : this._closeDrain}
        @keydown=${this._onOverlayKeydown(this._draining ? nothing : this._closeDrain)}
      >
        <div class="confirm-dialog" @click=${(e: Event) => e.stopPropagation()}>
          <h3>Drain Node</h3>
          ${
            result
              ? this._renderDrainResult(node, result)
              : html`
                  <p>
                    Cordon <span class="confirm-ref">${node}</span> and evict its pods.
                    PodDisruptionBudgets are honoured; blocked pods are retried until
                    the timeout.
                  </p>
                  <label class="drain-option">
                    <input
                      type="checkbox"
                      .checked=${opts.ignore_daemonsets}
                      ?disabled=${this._draining}
                      @change=${(e: Event) => {
                        this._drainOptions = {
                          ...opts,
                          ignore_daemonsets: (e.target as HTMLInputElement).checked,
                        };
                      }}
                    />
                    Ignore DaemonSet pods
                  </label>
                  <label class="drain-option">
                    <input
                      type="checkbox"
                      .checked=${opts.delete_emptydir_data}
                      ?disabled=${this._draining}
                      @change=${(e: Event) => {
                        this._drainOptions = {
                          ...opts,
                          delete_emptydir_data: (e.target as HTMLInputElement).checked,
                        };
                      }}
                    />
                    Evict pods with emptyDir data (the data is lost)
                  </label>
                  <label class="drain-option">
                    <input
                      type="checkbox"
                      .checked=${opts.force}
                      ?disabled=${this._draining}
                      @change=${(e: Event) => {
                        this._drainOptions = {
                          ...opts,
                          force: (e.target as HTMLInputElement).checked,
                        };
                      }}
                    />
                    Evict pods without a controller (they are not recreated)
                  </label>
                  <label class="drain-option">
                    Timeout
                    <input
                      class="drain-timeout"
                      type="number"
                      min="0"
                      max="3600"
                      .value=${String(opts.timeout)}
                      ?disabled=${this._draining}
                      @input=${(e: InputEvent) => {
                        const v = parseInt((e.target as HTMLInputElement).value, 10);
                        if (!isNaN(v) && v >= 0 && v <= 3600) {
                          this._drainOptions = { ...opts, timeout: v };
                        }
                      }}
                    />
                    s
                  </label>
                `
          }
          <div class="confirm-actions">
            ${
              result
                ? html`<button @click=${this._closeDrain}>Close</button>`
                : html`
                    <button @click=${this._closeDrain} ?disabled=${this._draining}>
                      Cancel
                    </button>
                    <button
                      class="drain-action"
                      @click=${this._confirmDrain}
                      ?disabled=${this._draining}
                    >
                      ${this._draining ? "Draining..." : "Drain"}
                    </button>
                  `
            }
          </div>
        </div>
      </div>
    `;
  }

  private _renderDrainResult(node: string, result: DrainResult) {
    return html`
      <p>
        <span class="confirm-ref">${node}</span> is cordoned. ${result.evicted.length}
        pod${result.evicted.length === 1 ? "" : "s"} evicted.
      </p>
      ${
        result.blocked.length
          ? html`<div class="drain-section blocked">
              Still blocked by a PodDisruptionBudget:
              <ul>
                ${result.blocked.map((p) => html`<li>${p}</li>`)}
              </ul>
            </div>`
          : nothing
      }
      ${
        result.evicted.length
          ? html`<div class="drain-section">
              Evicted:
              <ul>
                ${result.evicted.map((p) => html`<li>${p}</li>`)}
              </ul>
            </div>`
          : nothing
      }
      ${
        result.skipped.length
          ? html`<div class="drain-section">
              Skipped:
              <ul>
                ${result.skipped.map(
                  (s) =>
                    html`<li>${s.pod} (${SKIP_REASONS[s.reason] ?? s.reason})</li>`,
                )}
              </ul>
            </div>`
          : nothing
      }
    `;
  }

  private _renderCluster(cluster: ClusterNodes) {
    const filtered = this._getFilteredNodes(cluster.nodes);
    const readyCount = cluster.nodes.filter((n) => n.status === "Ready").length;

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
          ${
            filtered.length !== cluster.nodes.length
              ? html` &middot; showing ${filtered.length}`
              : nothing
          }
        </div>

        ${
          filtered.length === 0
            ? html`<div class="empty">No nodes match your filters.</div>`
            : filtered.map((node) => this._renderNode(cluster.entry_id, node))
        }
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
        <div
          class="node-row"
          role="button"
          tabindex="0"
          @click=${() => this._toggleNode(nodeKey)}
          @keydown=${(e: KeyboardEvent) => {
            if (e.key === "Enter" || e.key === " ") {
              e.preventDefault();
              this._toggleNode(nodeKey);
            }
          }}
        >
          <div class="node-name">
            <ha-icon
              icon=${expanded ? "mdi:chevron-down" : "mdi:chevron-right"}
            ></ha-icon>
            ${node.name}
            ${
              !node.schedulable
                ? html`<span class="badge badge-unschedulable">Unschedulable</span>`
                : nothing
            }
            ${
              conditions.length > 0
                ? html`<span class="badge badge-condition"
                    >${conditions.length}
                    condition${conditions.length > 1 ? "s" : ""}</span
                  >`
                : nothing
            }
          </div>
          <span
            class="badge ${node.status === "Ready" ? "badge-ready" : "badge-not-ready"}"
          >
            ${node.status}
          </span>
          <span class="node-ip">${node.internal_ip}</span>
          <div class="node-resources">
            ${
              hasMetrics
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
                    >${node.cpu_cores} CPU &middot; ${node.memory_capacity_gib}
                    GiB</span
                  >`
            }
          </div>
          <span class="node-age">${formatAge(node.creation_timestamp)}</span>
          ${
            isAdmin(this.hass)
              ? html`<div class="node-actions">
                  <button
                    class="action-btn ${node.schedulable ? "cordon" : "uncordon"}"
                    title=${node.schedulable ? "Cordon (stop scheduling new pods)" : "Uncordon"}
                    ?disabled=${this._actionInProgress.has(nodeKey)}
                    @click=${(e: Event) => {
                      e.stopPropagation();
                      this._setSchedulable(entryId, node, !node.schedulable);
                    }}
                  >
                    <ha-icon
                      icon=${node.schedulable ? "mdi:server-off" : "mdi:server"}
                    ></ha-icon>
                  </button>
                  <button
                    class="action-btn drain"
                    title="Drain (cordon and evict pods)"
                    @click=${(e: Event) => {
                      e.stopPropagation();
                      this._requestDrain(entryId, node);
                    }}
                  >
                    <ha-icon icon="mdi:tray-arrow-up"></ha-icon>
                  </button>
                </div>`
              : html`<div class="node-actions"></div>`
          }
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
          ${
            hasMetrics
              ? html`
                  <div class="detail-item">
                    <span class="detail-label">CPU Usage</span>
                    <span class="detail-value"
                      >${node.cpu_usage_millicores}m / ${node.cpu_cores * 1000}m</span
                    >
                  </div>
                `
              : nothing
          }
          <div class="detail-item">
            <span class="detail-label">Memory Capacity</span>
            <span class="detail-value">${node.memory_capacity_gib} GiB</span>
          </div>
          <div class="detail-item">
            <span class="detail-label">Memory Allocatable</span>
            <span class="detail-value">${node.memory_allocatable_gib} GiB</span>
          </div>
          ${
            hasMetrics
              ? html`
                  <div class="detail-item">
                    <span class="detail-label">Memory Usage</span>
                    <span class="detail-value"
                      >${memUsageGib} / ${node.memory_capacity_gib} GiB</span
                    >
                  </div>
                `
              : nothing
          }
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
        ${
          conditions.length > 0
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
            : nothing
        }
      </div>
    `;
  }
}
