import { html, css, nothing } from "lit";
import { customElement, state } from "lit/decorators.js";
import { K8sDataView } from "./base-view";
import { stateStyles, filterStyles, badgeStyles, tableStyles } from "../styles/shared";
import { formatAge, errorMessage } from "../utils/format";

interface IngressRule {
  host: string;
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
export class K8sNetwork extends K8sDataView<IngressesResponse> {
  @state() private _services: ServicesResponse | null = null;
  @state() private _ingressError: string | null = null;
  @state() private _servicesError: string | null = null;
  @state() private _searchQuery: string = "";
  @state() private _typeFilter: NetworkTypeFilter = "all";

  protected loadErrorFallback = "Failed to load network data";

  protected hasData(): boolean {
    return this._data !== null || this._services !== null;
  }

  protected async fetchData(): Promise<void> {
    // Each list fails on its own, so a missing RBAC rule for one resource
    // does not blank the other section.
    const [ingresses, services] = await Promise.allSettled([
      this.hass.callWS<IngressesResponse>({ type: "kubernetes/ingresses/list" }),
      this.hass.callWS<ServicesResponse>({ type: "kubernetes/services/list" }),
    ]);
    if (ingresses.status === "fulfilled") {
      this._data = ingresses.value;
      this._ingressError = null;
    } else {
      this._ingressError = errorMessage(
        ingresses.reason,
        "Failed to load ingress data",
      );
    }
    if (services.status === "fulfilled") {
      this._services = services.value;
      this._servicesError = null;
    } else {
      this._servicesError = errorMessage(
        services.reason,
        "Failed to load service data",
      );
    }
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

  static styles = [
    stateStyles,
    filterStyles,
    badgeStyles,
    tableStyles,
    css`
      /* stateStyles' .empty is 64px padding; network uses .empty for five
       in-section messages, where that much padding doubles up. */
      .empty {
        padding: 32px 16px;
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

      .badge-type-nodeport {
        background: rgba(var(--rgb-primary-color, 3, 169, 244), 0.15);
        color: var(--primary-color);
      }

      .badge-type-clusterip {
        background: rgba(var(--rgb-secondary-text-color, 114, 114, 114), 0.15);
        color: var(--secondary-text-color);
      }
    `,
  ];

  protected render() {
    if (this._loading) {
      return html`<div class="loading">
        <ha-circular-progress indeterminate></ha-circular-progress>
      </div>`;
    }

    if (this._ingressError && this._servicesError) {
      return html`
        <ha-card>
          <div class="error-card">
            <ha-icon icon="mdi:alert-circle"></ha-icon>
            <p>${this._ingressError}</p>
            <button class="retry-btn" @click=${() => this._loadData()}>Retry</button>
          </div>
        </ha-card>
      `;
    }

    const ingressClusters = this._data?.clusters ?? [];
    const serviceClusters = this._services?.clusters ?? [];
    const hasIngresses = ingressClusters.some((c) => c.ingresses.length > 0);
    const hasServices = serviceClusters.some((c) => c.services.length > 0);
    if (!this._ingressError && !this._servicesError && !hasIngresses && !hasServices) {
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
                this._ingressError
                  ? this._renderInlineError(this._ingressError)
                  : hasIngresses
                    ? ingressClusters.map((cluster) => this._renderCluster(cluster))
                    : html`<div class="empty">No ingresses found.</div>`
              }
            `
          : nothing
      }
      ${
        this._typeFilter !== "Ingress"
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
                    <td>${formatAge(ingress.creation_timestamp)}</td>
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
                    <td>${formatAge(svc.creation_timestamp)}</td>
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
