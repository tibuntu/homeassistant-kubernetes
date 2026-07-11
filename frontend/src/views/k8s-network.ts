import { LitElement, html, css, nothing, PropertyValues } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import type { HomeAssistant } from "../types/homeassistant";

interface IngressRule {
  host: string;
  path: string;
  service_name: string;
}

interface IngressData {
  name: string;
  namespace: string;
  ingress_class: string;
  rules: IngressRule[];
  tls_hosts: string[];
  urls: string[];
  creation_timestamp: string;
}

interface ClusterIngresses {
  entry_id: string;
  cluster_name: string;
  ingresses: IngressData[];
}

interface IngressesResponse {
  clusters: ClusterIngresses[];
}

@customElement("k8s-network")
export class K8sNetwork extends LitElement {
  @property({ attribute: false }) public hass!: HomeAssistant;

  @state() private _data: IngressesResponse | null = null;
  @state() private _loading = true;
  @state() private _error: string | null = null;
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
      const result: IngressesResponse = await this.hass.callWS({
        type: "kubernetes/ingresses/list",
      });
      this._data = result;
    } catch (err: any) {
      this._error = err.message || "Failed to load ingress data";
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

  private _getFilteredIngresses(ingresses: IngressData[]): IngressData[] {
    if (!this._searchQuery) return ingresses;
    const q = this._searchQuery.toLowerCase();
    return ingresses.filter(
      (i) =>
        i.name.toLowerCase().includes(q) ||
        i.namespace.toLowerCase().includes(q) ||
        i.rules.some((r) => (r.host || "").toLowerCase().includes(q)),
    );
  }

  private _services(ingress: IngressData): string {
    return [...new Set(ingress.rules.map((r) => r.service_name))]
      .filter(Boolean)
      .join(", ");
  }

  private _hasTls(ingress: IngressData): boolean {
    return (
      ingress.tls_hosts.length > 0 || ingress.urls.some((u) => u.startsWith("https://"))
    );
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

    .ingress-table {
      width: 100%;
      border-collapse: collapse;
      font-size: 13px;
    }

    .ingress-table th {
      text-align: left;
      padding: 10px 12px;
      color: var(--secondary-text-color);
      font-weight: 500;
      border-bottom: 2px solid var(--divider-color);
      white-space: nowrap;
    }

    .ingress-table td {
      padding: 8px 12px;
      border-bottom: 1px solid var(--divider-color);
      vertical-align: middle;
    }

    .ingress-table tr:last-child td {
      border-bottom: none;
    }

    .ingress-table tr:hover td {
      background: rgba(var(--rgb-primary-color, 3, 169, 244), 0.04);
    }

    .url-link {
      display: block;
      color: var(--primary-color);
      text-decoration: none;
      white-space: nowrap;
    }

    .url-link:hover {
      text-decoration: underline;
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

    .badge-tls {
      background: rgba(var(--rgb-success-color, 76, 175, 80), 0.15);
      color: var(--success-color, #4caf50);
    }

    .badge-plain {
      background: rgba(var(--rgb-warning-color, 255, 152, 0), 0.15);
      color: var(--warning-color, #ff9800);
    }
  `;

  protected render() {
    if (this._loading) {
      return html`<div class="loading">
        <ha-circular-progress indeterminate></ha-circular-progress>
      </div>`;
    }

    if (this._error) {
      return html`
        <div class="error-card">
          <ha-icon icon="mdi:alert-circle"></ha-icon>
          <p>${this._error}</p>
          <button class="retry-btn" @click=${() => this._loadData()}>Retry</button>
        </div>
      `;
    }

    const clusters = this._data?.clusters ?? [];
    if (!clusters.length || clusters.every((c) => !c.ingresses.length)) {
      return html`<div class="empty">No ingresses found.</div>`;
    }

    return html`
      <div class="filters">
        <input
          class="search-input"
          type="text"
          placeholder="Search ingresses…"
          .value=${this._searchQuery}
          @input=${(e: InputEvent) =>
            (this._searchQuery = (e.target as HTMLInputElement).value)}
        />
      </div>
      ${clusters.map((cluster) => this._renderCluster(cluster))}
    `;
  }

  private _renderCluster(cluster: ClusterIngresses) {
    if (!cluster.ingresses.length) return nothing;
    const ingresses = this._getFilteredIngresses(cluster.ingresses);

    return html`
      <div class="cluster-section">
        ${
          this._data!.clusters.length > 1
            ? html`<div class="cluster-name">${cluster.cluster_name}</div>`
            : nothing
        }
        ${
          ingresses.length === 0
            ? html`<div class="empty">No ingresses match your search.</div>`
            : this._renderTable(ingresses)
        }
      </div>
    `;
  }

  private _renderTable(ingresses: IngressData[]) {
    return html`
      <table class="ingress-table">
        <thead>
          <tr>
            <th>Name</th>
            <th>Namespace</th>
            <th>Class</th>
            <th>URLs</th>
            <th>Service</th>
            <th>TLS</th>
            <th>Age</th>
          </tr>
        </thead>
        <tbody>
          ${ingresses.map(
            (ingress) => html`
              <tr>
                <td>${ingress.name}</td>
                <td>${ingress.namespace}</td>
                <td>${ingress.ingress_class || "—"}</td>
                <td>${this._renderUrls(ingress)}</td>
                <td>${this._services(ingress) || "—"}</td>
                <td>${this._renderTlsBadge(ingress)}</td>
                <td>${this._formatAge(ingress.creation_timestamp)}</td>
              </tr>
            `,
          )}
        </tbody>
      </table>
    `;
  }

  private _renderUrls(ingress: IngressData) {
    if (!ingress.urls.length) return "—";
    return ingress.urls.map(
      (url) => html`
        <a class="url-link" href=${url} target="_blank" rel="noopener noreferrer"
          >${url}</a
        >
      `,
    );
  }

  private _renderTlsBadge(ingress: IngressData) {
    return this._hasTls(ingress)
      ? html`<span class="badge badge-tls">TLS</span>`
      : html`<span class="badge badge-plain">HTTP</span>`;
  }
}
