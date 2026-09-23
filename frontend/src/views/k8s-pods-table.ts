import { html, css, nothing, PropertyValues } from "lit";
import { customElement, state } from "lit/decorators.js";
import { K8sDataView } from "./base-view";
import {
  stateStyles,
  filterStyles,
  badgeStyles,
  dialogStyles,
  tableStyles,
} from "../styles/shared";
import { formatAge, errorMessage } from "../utils/format";

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

const TOGGLEABLE_COLUMNS = [
  { key: "ready", label: "Ready" },
  { key: "restarts", label: "Restarts" },
  { key: "node", label: "Node" },
  { key: "ip", label: "IP" },
  { key: "owner", label: "Owner" },
  { key: "age", label: "Age" },
] as const;
type ColumnKey = (typeof TOGGLEABLE_COLUMNS)[number]["key"];
const ALL_COLUMN_KEYS: Set<ColumnKey> = new Set(TOGGLEABLE_COLUMNS.map((c) => c.key));
const STORAGE_KEY = "k8s-pods-columns";

function loadColumnPrefs(): Set<ColumnKey> {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored) {
      const parsed = JSON.parse(stored) as string[];
      const valid = parsed.filter((k) => ALL_COLUMN_KEYS.has(k as ColumnKey));
      if (valid.length) return new Set(valid as ColumnKey[]);
    }
  } catch {
    // localStorage unavailable or corrupt — use defaults
  }
  return new Set(ALL_COLUMN_KEYS);
}

function saveColumnPrefs(cols: Set<ColumnKey>): void {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify([...cols]));
  } catch {
    // localStorage unavailable — no-op
  }
}

@customElement("k8s-pods-table")
export class K8sPodsTable extends K8sDataView<PodsResponse> {
  @state() private _searchQuery: string = "";
  @state() private _phaseFilter: string = "all";
  @state() private _namespaceFilter: string = "all";
  @state() private _sortField: string = "name";
  @state() private _sortAsc: boolean = true;
  @state() private _deleteConfirm: PodIdentifier | null = null;
  @state() private _deleting = false;
  @state() private _visibleColumns: Set<ColumnKey> = loadColumnPrefs();
  @state() private _columnMenuOpen = false;

  protected loadErrorFallback = "Failed to load pods data";

  private _boundCloseMenu = () => {
    this._columnMenuOpen = false;
  };

  protected firstUpdated(changedProps: PropertyValues): void {
    super.firstUpdated(changedProps);
    document.addEventListener("click", this._boundCloseMenu);
  }

  disconnectedCallback(): void {
    super.disconnectedCallback();
    document.removeEventListener("click", this._boundCloseMenu);
  }

  protected async fetchData(): Promise<void> {
    const result: PodsResponse = await this.hass.callWS({
      type: "kubernetes/pods/list",
    });
    this._data = result;
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

    filtered = [...filtered].sort((a, b) => {
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

  private _handleSortKeydown(e: KeyboardEvent, field: string): void {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      this._handleSort(field);
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
    } catch (err: unknown) {
      this._error = errorMessage(err, "Failed to delete pod");
      this._deleteConfirm = null;
    } finally {
      this._deleting = false;
    }
  }

  private _sortIcon(field: string): string {
    if (this._sortField !== field) return "";
    return this._sortAsc ? "mdi:arrow-up" : "mdi:arrow-down";
  }

  static styles = [
    stateStyles,
    filterStyles,
    badgeStyles,
    dialogStyles,
    tableStyles,
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

      .column-menu-wrapper {
        position: relative;
        margin-left: auto;
      }

      .column-toggle-btn {
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 6px;
        border: 1px solid var(--divider-color);
        border-radius: 8px;
        background: transparent;
        color: var(--secondary-text-color);
        cursor: pointer;
        --mdc-icon-size: 18px;
      }

      .column-toggle-btn:hover {
        color: var(--primary-color);
        border-color: var(--primary-color);
      }

      .column-menu {
        position: absolute;
        top: 100%;
        right: 0;
        margin-top: 4px;
        background: var(--card-background-color, #fff);
        border: 1px solid var(--divider-color);
        border-radius: 8px;
        padding: 8px 0;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        z-index: 10;
        min-width: 140px;
      }

      .column-option {
        display: flex;
        align-items: center;
        gap: 8px;
        padding: 6px 14px;
        font-size: 13px;
        color: var(--primary-text-color);
        cursor: pointer;
        white-space: nowrap;
      }

      .column-option:hover {
        background: rgba(var(--rgb-primary-color, 3, 169, 244), 0.06);
      }

      .column-option input[type="checkbox"] {
        accent-color: var(--primary-color);
      }
    `,
  ];

  protected render() {
    const state = this.renderState(!this._data?.clusters.length);
    if (state !== nothing) return state;

    return html`
      ${this._data!.clusters.map((c) => this._renderCluster(c))}
      ${this._deleteConfirm ? this._renderDeleteDialog() : nothing}
    `;
  }

  private _renderCluster(cluster: ClusterPods) {
    const filtered = this._getFilteredPods(cluster.pods);
    const namespaces = this._getNamespaces(cluster.pods);
    const phases = [...new Set(cluster.pods.map((p) => p.phase))].sort();

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
            placeholder="Search pods..."
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
          ${this._renderColumnMenu()}
        </div>

        <div class="pod-count">${filtered.length}/${cluster.pods.length} pods</div>

        ${
          filtered.length === 0
            ? html`<div class="empty">No pods match your filters.</div>`
            : html`
                <ha-card>
                  <div class="table-wrapper">
                    <table class="pods-table">
                      <thead>
                        <tr>
                          <th
                            role="button"
                            tabindex="0"
                            @click=${() => this._handleSort("namespace")}
                            @keydown=${(e: KeyboardEvent) =>
                              this._handleSortKeydown(e, "namespace")}
                          >
                            Namespace
                            ${
                              this._sortIcon("namespace")
                                ? html`<ha-icon
                                    icon=${this._sortIcon("namespace")}
                                  ></ha-icon>`
                                : nothing
                            }
                          </th>
                          <th
                            role="button"
                            tabindex="0"
                            @click=${() => this._handleSort("name")}
                            @keydown=${(e: KeyboardEvent) =>
                              this._handleSortKeydown(e, "name")}
                          >
                            Name
                            ${
                              this._sortIcon("name")
                                ? html`<ha-icon
                                    icon=${this._sortIcon("name")}
                                  ></ha-icon>`
                                : nothing
                            }
                          </th>
                          <th
                            role="button"
                            tabindex="0"
                            @click=${() => this._handleSort("phase")}
                            @keydown=${(e: KeyboardEvent) =>
                              this._handleSortKeydown(e, "phase")}
                          >
                            Phase
                            ${
                              this._sortIcon("phase")
                                ? html`<ha-icon
                                    icon=${this._sortIcon("phase")}
                                  ></ha-icon>`
                                : nothing
                            }
                          </th>
                          ${this._colVisible("ready") ? html`<th>Ready</th>` : nothing}
                          ${
                            this._colVisible("restarts")
                              ? html`<th
                                  role="button"
                                  tabindex="0"
                                  @click=${() => this._handleSort("restarts")}
                                  @keydown=${(e: KeyboardEvent) =>
                                    this._handleSortKeydown(e, "restarts")}
                                >
                                  Restarts
                                  ${this._sortIcon("restarts") ? html`<ha-icon icon=${this._sortIcon("restarts")}></ha-icon>` : nothing}
                                </th>`
                              : nothing
                          }
                          ${
                            this._colVisible("node")
                              ? html`<th
                                  role="button"
                                  tabindex="0"
                                  @click=${() => this._handleSort("node_name")}
                                  @keydown=${(e: KeyboardEvent) =>
                                    this._handleSortKeydown(e, "node_name")}
                                >
                                  Node
                                  ${this._sortIcon("node_name") ? html`<ha-icon icon=${this._sortIcon("node_name")}></ha-icon>` : nothing}
                                </th>`
                              : nothing
                          }
                          ${this._colVisible("ip") ? html`<th>IP</th>` : nothing}
                          ${this._colVisible("owner") ? html`<th>Owner</th>` : nothing}
                          ${
                            this._colVisible("age")
                              ? html`<th
                                  role="button"
                                  tabindex="0"
                                  @click=${() => this._handleSort("age")}
                                  @keydown=${(e: KeyboardEvent) =>
                                    this._handleSortKeydown(e, "age")}
                                >
                                  Age
                                  ${this._sortIcon("age") ? html`<ha-icon icon=${this._sortIcon("age")}></ha-icon>` : nothing}
                                </th>`
                              : nothing
                          }
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
              `
        }
      </div>
    `;
  }

  private _colVisible(key: ColumnKey): boolean {
    return this._visibleColumns.has(key);
  }

  private _toggleColumn(key: ColumnKey): void {
    const updated = new Set(this._visibleColumns);
    if (updated.has(key)) {
      updated.delete(key);
    } else {
      updated.add(key);
    }
    this._visibleColumns = updated;
    saveColumnPrefs(updated);
  }

  private _renderColumnMenu() {
    return html`
      <div class="column-menu-wrapper">
        <button
          class="column-toggle-btn"
          title="Toggle columns"
          @click=${(e: Event) => {
            e.stopPropagation();
            this._columnMenuOpen = !this._columnMenuOpen;
          }}
        >
          <ha-icon icon="mdi:table-column"></ha-icon>
        </button>
        ${
          this._columnMenuOpen
            ? html`
                <div class="column-menu" @click=${(e: Event) => e.stopPropagation()}>
                  ${TOGGLEABLE_COLUMNS.map(
                    (col) => html`
                      <label class="column-option">
                        <input
                          type="checkbox"
                          .checked=${this._visibleColumns.has(col.key)}
                          @change=${() => this._toggleColumn(col.key)}
                        />
                        ${col.label}
                      </label>
                    `,
                  )}
                </div>
              `
            : nothing
        }
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
        ${this._colVisible("ready") ? html`<td>${pod.ready_containers}/${pod.total_containers}</td>` : nothing}
        ${this._colVisible("restarts") ? html`<td class=${pod.restart_count > 5 ? "restart-warn" : ""}>${pod.restart_count}</td>` : nothing}
        ${this._colVisible("node") ? html`<td>${pod.node_name}</td>` : nothing}
        ${this._colVisible("ip") ? html`<td class="mono">${pod.pod_ip}</td>` : nothing}
        ${this._colVisible("owner") ? html`<td>${pod.owner_kind !== "N/A" ? html`<span class="owner-info">${pod.owner_kind}/${pod.owner_name}</span>` : html`<span class="owner-info">-</span>`}</td>` : nothing}
        ${this._colVisible("age") ? html`<td>${formatAge(pod.creation_timestamp)}</td>` : nothing}
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
            <span class="confirm-ref">${confirm.namespace}/${confirm.pod_name}</span>?
            This action cannot be undone.
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
