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

interface ServicePort {
  name: string | null;
  port: number;
  target_port: number | string | null;
  node_port: number | null;
  protocol: string;
}

interface ServiceData {
  name: string;
  namespace: string;
  type: string;
  cluster_ip: string;
  external_ips: string[];
  ports: ServicePort[];
  urls: string[];
  creation_timestamp: string;
}

interface ClusterServices {
  entry_id: string;
  cluster_name: string;
  services: ServiceData[];
}

interface ServicesResponse {
  clusters: ClusterServices[];
}

const NETWORK_TYPES = [
  "Ingress",
  "LoadBalancer",
  "NodePort",
  "ClusterIP",
  "ExternalName",
] as const;
type NetworkTypeFilter = "all" | (typeof NETWORK_TYPES)[number];

@customElement("k8s-network")
export class K8sNetwork extends LitElement {
  @property({ attribute: false }) public hass!: HomeAssistant;

  @state() private _data: IngressesResponse | null = null;
  @state() private _services: ServicesResponse | null = null;
  @state() private _loading = true;
  @state() private _error: string | null = null;
  @state() private _servicesError: string | null = null;
  @state() private _searchQuery: string = "";
  @state() private _typeFilter: NetworkTypeFilter = "all";

  private _refreshInterval?: ReturnType<typeof setInterval>;
  private _loadingInFlight = false;
  private _boundVisibilityHandler = this._handleVisibilityChange.bind(this);
  private _unsubUpdates?: () => Promise<void>;
  private _updateDebounce?: ReturnType<typeof setTimeout>;

  protected firstUpdated(_changedProps: PropertyValues): void {
    this._loadData();
    this._startPolling();
    document.addEventListener("visibilitychange", this._boundVisibilityHandler);
    void this._subscribeUpdates();
  }

  disconnectedCallback(): void {
    super.disconnectedCallback();
    this._stopPolling();
    document.removeEventListener("visibilitychange", this._boundVisibilityHandler);
    void this._unsubUpdates?.().catch(() => {});
    this._unsubUpdates = undefined;
    if (this._updateDebounce) {
      clearTimeout(this._updateDebounce);
      this._updateDebounce = undefined;
    }
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
      this._refreshInterval = setInterval(() => this._loadData(), 60000);
    }
  }

  private _stopPolling(): void {
    if (this._refreshInterval) {
      clearInterval(this._refreshInterval);
      this._refreshInterval = undefined;
    }
  }

  private async _subscribeUpdates(): Promise<void> {
    try {
      const unsub = await this.hass.connection.subscribeMessage(
        () => this._scheduleLoad(),
        { type: "kubernetes/subscribe_updates" },
      );
      if (!this.isConnected) {
        void unsub().catch(() => {});
        return;
      }
      this._unsubUpdates = unsub;
    } catch {
      // Backend without subscription support — interval polling covers it.
    }
  }

  private _scheduleLoad(): void {
    if (document.hidden) return;
    if (this._updateDebounce) return;
    this._updateDebounce = setTimeout(() => {
      this._updateDebounce = undefined;
      this._loadData();
    }, 1000);
  }

  private async _loadData(): Promise<void> {
    if (this._loadingInFlight) return;
    this._loadingInFlight = true;
    if (!this._data && !this._services) {
      this._loading = true;
    }
    // Each list fails on its own, so a missing RBAC rule for one resource
    // does not blank the other section.
    const [ingresses, services] = await Promise.allSettled([
      this.hass.callWS<IngressesResponse>({ type: "kubernetes/ingresses/list" }),
      this.hass.callWS<ServicesResponse>({ type: "kubernetes/services/list" }),
    ]);
    if (ingresses.status === "fulfilled") {
      this._data = ingresses.value;
      this._error = null;
    } else {
      this._error = ingresses.reason?.message || "Failed to load ingress data";
    }
    if (services.status === "fulfilled") {
      this._services = services.value;
      this._servicesError = null;
    } else {
      this._servicesError = services.reason?.message || "Failed to load service data";
    }
    this._loading = false;
    this._loadingInFlight = false;
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

  private _getFilteredServices(services: ServiceData[]): ServiceData[] {
    let filtered = services;
    if (this._typeFilter !== "all") {
      filtered = filtered.filter((s) => s.type === this._typeFilter);
    }
    if (this._searchQuery) {
      const q = this._searchQuery.toLowerCase();
      filtered = filtered.filter(
        (s) =>
          s.name.toLowerCase().includes(q) ||
          s.namespace.toLowerCase().includes(q) ||
          s.external_ips.some((ip) => ip.toLowerCase().includes(q)),
      );
    }
    return filtered;
  }

  private _services_of(ingress: IngressData): string {
    return [...new Set(ingress.rules.map((r) => r.service_name))]
      .filter(Boolean)
      .join(", ");
  }

  private _hasTls(ingress: IngressData): boolean {
    return (
      ingress.tls_hosts.length > 0 || ingress.urls.some((u) => u.startsWith("https://"))
    );
  }

  private _formatPort(p: ServicePort): string {
    const target =
      p.target_port != null && String(p.target_port) !== String(p.port)
        ? `→${p.target_port}`
        : "";
    const node = p.node_port ? ` (node ${p.node_port})` : "";
    return `${p.port}${target}/${p.protocol}${node}`;
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

    .inline-error {
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 10px 16px;
      margin-bottom: 16px;
      border-radius: 8px;
      background: rgba(var(--rgb-error-color, 244, 67, 54), 0.1);
      color: var(--error-color, #f44336);
      font-size: 14px;
      --mdc-icon-size: 18px;
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
      padding: 32px 16px;
      color: var(--secondary-text-color);
      font-size: 16px;
    }

    .section-title {
      font-size: 18px;
      font-weight: 500;
      color: var(--primary-text-color);
      margin: 24px 0 12px;
    }

    .section-title:first-of-type {
      margin-top: 0;
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

    .network-table {
      width: 100%;
      border-collapse: collapse;
      font-size: 13px;
    }

    .network-table th {
      text-align: left;
      padding: 10px 12px;
      color: var(--secondary-text-color);
      font-weight: 500;
      border-bottom: 2px solid var(--divider-color);
      white-space: nowrap;
    }

    .network-table td {
      padding: 8px 12px;
      border-bottom: 1px solid var(--divider-color);
      vertical-align: middle;
    }

    .network-table tr:last-child td {
      border-bottom: none;
    }

    .network-table tr:hover td {
      background: rgba(var(--rgb-primary-color, 3, 169, 244), 0.04);
    }

    .mono {
      font-family: monospace;
      white-space: nowrap;
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

    .badge-tls,
    .badge-type-loadbalancer {
      background: rgba(var(--rgb-success-color, 76, 175, 80), 0.15);
      color: var(--success-color, #4caf50);
    }

    .badge-plain,
    .badge-type-externalname {
      background: rgba(var(--rgb-warning-color, 255, 152, 0), 0.15);
      color: var(--warning-color, #ff9800);
    }

    .badge-type-nodeport {
      background: rgba(var(--rgb-primary-color, 3, 169, 244), 0.15);
      color: var(--primary-color);
    }

    .badge-type-clusterip {
      background: rgba(var(--rgb-secondary-text-color, 114, 114, 114), 0.15);
      color: var(--secondary-text-color);
    }

    .table-wrapper {
      overflow-x: auto;
    }
  `;

  protected render() {
    if (this._loading) {
      return html`<div class="loading">
        <ha-circular-progress indeterminate></ha-circular-progress>
      </div>`;
    }

    if (this._error && this._servicesError) {
      return html`
        <ha-card>
          <div class="error-card">
            <ha-icon icon="mdi:alert-circle"></ha-icon>
            <p>${this._error}</p>
            <button class="retry-btn" @click=${() => this._loadData()}>Retry</button>
          </div>
        </ha-card>
      `;
    }

    const ingressClusters = this._data?.clusters ?? [];
    const serviceClusters = this._services?.clusters ?? [];
    const hasIngresses = ingressClusters.some((c) => c.ingresses.length > 0);
    const hasServices = serviceClusters.some((c) => c.services.length > 0);
    if (!this._error && !this._servicesError && !hasIngresses && !hasServices) {
      return html`<div class="empty">No ingresses or services found.</div>`;
    }

    return html`
      <div class="filters">
        <input
          class="search-input"
          type="text"
          placeholder="Search ingresses and services…"
          .value=${this._searchQuery}
          @input=${(e: InputEvent) =>
            (this._searchQuery = (e.target as HTMLInputElement).value)}
        />
        <select
          class="filter-select"
          .value=${this._typeFilter}
          @change=${(e: Event) => {
            this._typeFilter = (e.target as HTMLSelectElement)
              .value as NetworkTypeFilter;
          }}
        >
          <option value="all">All types</option>
          ${NETWORK_TYPES.map((t) => html`<option value=${t}>${t}</option>`)}
        </select>
      </div>

      ${
        this._typeFilter === "all" || this._typeFilter === "Ingress"
          ? html`
              <h2 class="section-title">Ingresses</h2>
              ${
                this._error
                  ? this._renderInlineError(this._error)
                  : hasIngresses
                    ? ingressClusters.map((cluster) => this._renderCluster(cluster))
                    : html`<div class="empty">No ingresses found.</div>`
              }
            `
          : nothing
      }
      ${
        this._typeFilter === "all" || this._typeFilter !== "Ingress"
          ? html`
              <h2 class="section-title">Services</h2>
              ${
                this._servicesError
                  ? this._renderInlineError(this._servicesError)
                  : hasServices
                    ? serviceClusters.map((cluster) =>
                        this._renderServiceCluster(cluster),
                      )
                    : html`<div class="empty">No services found.</div>`
              }
            `
          : nothing
      }
    `;
  }

  private _renderInlineError(message: string) {
    return html`
      <div class="inline-error">
        <ha-icon icon="mdi:alert-circle"></ha-icon>
        <span>${message}</span>
      </div>
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
      <ha-card>
        <div class="table-wrapper">
          <table class="network-table">
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
                    <td>${this._renderUrls(ingress.urls)}</td>
                    <td>${this._services_of(ingress) || "—"}</td>
                    <td>${this._renderTlsBadge(ingress)}</td>
                    <td>${this._formatAge(ingress.creation_timestamp)}</td>
                  </tr>
                `,
              )}
            </tbody>
          </table>
        </div>
      </ha-card>
    `;
  }

  private _renderServiceCluster(cluster: ClusterServices) {
    if (!cluster.services.length) return nothing;
    const services = this._getFilteredServices(cluster.services);

    return html`
      <div class="cluster-section">
        ${
          this._services!.clusters.length > 1
            ? html`<div class="cluster-name">${cluster.cluster_name}</div>`
            : nothing
        }
        ${
          services.length === 0
            ? html`<div class="empty">No services match your filters.</div>`
            : this._renderServicesTable(services)
        }
      </div>
    `;
  }

  private _renderServicesTable(services: ServiceData[]) {
    return html`
      <ha-card>
        <div class="table-wrapper">
          <table class="network-table">
            <thead>
              <tr>
                <th>Name</th>
                <th>Namespace</th>
                <th>Type</th>
                <th>Cluster IP</th>
                <th>External</th>
                <th>Ports</th>
                <th>Age</th>
              </tr>
            </thead>
            <tbody>
              ${services.map(
                (svc) => html`
                  <tr>
                    <td>${svc.name}</td>
                    <td>${svc.namespace}</td>
                    <td>
                      <span class="badge badge-type-${svc.type.toLowerCase()}"
                        >${svc.type}</span
                      >
                    </td>
                    <td class="mono">${svc.cluster_ip || "—"}</td>
                    <td>${this._renderExternal(svc)}</td>
                    <td class="mono">
                      ${
                        svc.ports.length
                          ? svc.ports.map(
                              (p) => html`<div>${this._formatPort(p)}</div>`,
                            )
                          : "—"
                      }
                    </td>
                    <td>${this._formatAge(svc.creation_timestamp)}</td>
                  </tr>
                `,
              )}
            </tbody>
          </table>
        </div>
      </ha-card>
    `;
  }

  private _renderExternal(svc: ServiceData) {
    if (svc.urls.length) return this._renderUrls(svc.urls);
    if (svc.external_ips.length) {
      return svc.external_ips.map((ip) => html`<div class="mono">${ip}</div>`);
    }
    return "—";
  }

  private _renderUrls(urls: string[]) {
    if (!urls.length) return "—";
    return urls.map(
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
