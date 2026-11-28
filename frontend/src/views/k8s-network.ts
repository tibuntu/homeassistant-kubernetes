import { html, css, nothing, PropertyValues } from "lit";
import { customElement, state } from "lit/decorators.js";
import { oneOf, queryParam } from "../utils/nav";
import { K8sDataView } from "./base-view";
import {
  stateStyles,
  filterStyles,
  badgeStyles,
  tableStyles,
  clusterStyles,
} from "../styles/shared";
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

interface HTTPRouteParentRef {
  name: string;
  namespace: string;
  section_name: string;
}

interface HTTPRouteMatch {
  path_type: string;
  path_value: string;
  method: string;
}

interface HTTPRouteBackendRef {
  name: string;
  namespace: string;
  port: number | string;
}

interface HTTPRouteRule {
  matches: HTTPRouteMatch[];
  backend_refs: HTTPRouteBackendRef[];
}

interface HTTPRouteData {
  name: string;
  namespace: string;
  hostnames: string[];
  parent_refs: HTTPRouteParentRef[];
  rules: HTTPRouteRule[];
  urls: string[];
  accepted: boolean;
  resolved_refs: boolean;
  creation_timestamp: string;
}

interface ClusterHTTPRoutes {
  entry_id: string;
  cluster_name: string;
  httproutes: HTTPRouteData[];
}

interface HTTPRoutesResponse {
  clusters: ClusterHTTPRoutes[];
}

interface CertificateData {
  name: string;
  namespace: string;
  not_after: string | null;
  renewal_time: string | null;
  ready: boolean;
  reason: string | null;
  message: string | null;
  issuer_name: string;
  issuer_kind: string;
  dns_names: string[];
  secret_name: string;
}

interface ClusterCertificates {
  entry_id: string;
  cluster_name: string;
  certificates: CertificateData[];
}

interface CertificatesResponse {
  clusters: ClusterCertificates[];
}

const RENEWAL_GRACE_MS = 24 * 3600 * 1000;

/** Status badge text; mirrors `alerts.certificate_problems` in the backend. */
function certificateStatus(cert: CertificateData): string {
  const now = Date.now();
  if (cert.not_after && Date.parse(cert.not_after) < now) return "Expired";
  if (!cert.ready) return "Not Ready";
  if (cert.renewal_time && Date.parse(cert.renewal_time) < now - RENEWAL_GRACE_MS) {
    return "Renewal Overdue";
  }
  return "Ready";
}

/** Time until an ISO timestamp as "in 5d" / "3h ago". */
function formatUntil(iso: string): string {
  const diff = Date.parse(iso) - Date.now();
  const abs = Math.abs(diff) / 1000;
  const text =
    abs < 3600
      ? `${Math.floor(abs / 60)}m`
      : abs < 86400
        ? `${Math.floor(abs / 3600)}h`
        : `${Math.floor(abs / 86400)}d`;
  return diff >= 0 ? `in ${text}` : `${text} ago`;
}

const NETWORK_TYPES = [
  "Ingress",
  "HTTPRoute",
  "Certificate",
  "LoadBalancer",
  "NodePort",
  "ClusterIP",
  "ExternalName",
] as const;
// "Services" shows every service type and hides the ingress/HTTPRoute/
// Certificate sections.
type NetworkTypeFilter = "all" | "Services" | (typeof NETWORK_TYPES)[number];

@customElement("k8s-network")
export class K8sNetwork extends K8sDataView<IngressesResponse> {
  @state() private _services: ServicesResponse | null = null;
  @state() private _httproutes: HTTPRoutesResponse | null = null;
  @state() private _certificates: CertificatesResponse | null = null;
  @state() private _ingressError: string | null = null;
  @state() private _servicesError: string | null = null;
  @state() private _httprouteError: string | null = null;
  @state() private _certificateError: string | null = null;
  @state() private _searchQuery: string = "";
  @state() private _typeFilter: NetworkTypeFilter = "all";
  protected tab = "network";

  protected readQuery(): void {
    this._searchQuery = queryParam("search") ?? "";
    this._typeFilter = oneOf<NetworkTypeFilter>(
      queryParam("type"),
      ["all", "Services", ...NETWORK_TYPES],
      "all",
    );
  }

  protected loadErrorFallback = "Failed to load network data";

  protected willUpdate(changed: PropertyValues): void {
    if (changed.has("_typeFilter") || changed.has("_searchQuery")) {
      this._syncQuery({
        search: this._searchQuery,
        type: this._typeFilter === "all" ? "" : this._typeFilter,
      });
    }
  }

  protected hasData(): boolean {
    return (
      this._data !== null ||
      this._services !== null ||
      this._httproutes !== null ||
      this._certificates !== null
    );
  }

  protected async fetchData(): Promise<void> {
    // Each list fails on its own, so a missing RBAC rule (or, for
    // HTTPRoutes and Certificates, an absent CRD) for one resource does not
    // blank the other sections.
    const [ingresses, services, httproutes, certificates] = await Promise.allSettled([
      this.hass.callWS<IngressesResponse>({ type: "kubernetes/ingresses/list" }),
      this.hass.callWS<ServicesResponse>({ type: "kubernetes/services/list" }),
      this.hass.callWS<HTTPRoutesResponse>({ type: "kubernetes/httproutes/list" }),
      this.hass.callWS<CertificatesResponse>({ type: "kubernetes/certificates/list" }),
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
    if (httproutes.status === "fulfilled") {
      this._httproutes = httproutes.value;
      this._httprouteError = null;
    } else {
      this._httprouteError = errorMessage(
        httproutes.reason,
        "Failed to load HTTPRoute data",
      );
    }
    if (certificates.status === "fulfilled") {
      this._certificates = certificates.value;
      this._certificateError = null;
    } else {
      this._certificateError = errorMessage(
        certificates.reason,
        "Failed to load certificate data",
      );
    }
    // Every list failed: let the base class show its full-page error card.
    if (
      ingresses.status === "rejected" &&
      this._servicesError &&
      this._httprouteError &&
      this._certificateError
    ) {
      throw ingresses.reason;
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
    if (
      this._typeFilter !== "all" &&
      this._typeFilter !== "Services" &&
      this._typeFilter !== "Ingress" &&
      this._typeFilter !== "HTTPRoute" &&
      this._typeFilter !== "Certificate"
    ) {
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

  private _getFilteredHTTPRoutes(httproutes: HTTPRouteData[]): HTTPRouteData[] {
    if (!this._searchQuery) return httproutes;
    const q = this._searchQuery.toLowerCase();
    return httproutes.filter(
      (r) =>
        r.name.toLowerCase().includes(q) ||
        r.namespace.toLowerCase().includes(q) ||
        r.hostnames.some((h) => h.toLowerCase().includes(q)),
    );
  }

  private _getFilteredCertificates(certificates: CertificateData[]): CertificateData[] {
    if (!this._searchQuery) return certificates;
    const q = this._searchQuery.toLowerCase();
    return certificates.filter(
      (c) =>
        c.name.toLowerCase().includes(q) ||
        c.namespace.toLowerCase().includes(q) ||
        c.dns_names.some((d) => d.toLowerCase().includes(q)),
    );
  }

  private _gatewaysOf(httproute: HTTPRouteData): string {
    return (
      [...new Set(httproute.parent_refs.map((p) => p.name))]
        .filter(Boolean)
        .join(", ") || "—"
    );
  }

  private _backendsOf(httproute: HTTPRouteData): string {
    const names = httproute.rules.flatMap((rule) =>
      rule.backend_refs.map((b) => b.name),
    );
    return [...new Set(names)].filter(Boolean).join(", ") || "—";
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
    clusterStyles,
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

      .secondary {
        color: var(--secondary-text-color);
        font-size: 12px;
        white-space: nowrap;
      }

      .badge-type-clusterip {
        background: rgba(var(--rgb-secondary-text-color, 114, 114, 114), 0.15);
        color: var(--secondary-text-color);
      }
    `,
  ];

  protected render() {
    const state = this.renderState(false);
    if (state !== nothing) return state;

    const ingressClusters = this._data?.clusters ?? [];
    const serviceClusters = this._services?.clusters ?? [];
    const httprouteClusters = this._httproutes?.clusters ?? [];
    const hasIngresses = ingressClusters.some((c) => c.ingresses.length > 0);
    const hasServices = serviceClusters.some((c) => c.services.length > 0);
    const hasHTTPRoutes = httprouteClusters.some((c) => c.httproutes.length > 0);
    const certificateClusters = this._certificates?.clusters ?? [];
    const hasCertificates = certificateClusters.some((c) => c.certificates.length > 0);
    if (
      !this._ingressError &&
      !this._servicesError &&
      !this._httprouteError &&
      !this._certificateError &&
      !hasIngresses &&
      !hasServices &&
      !hasHTTPRoutes &&
      !hasCertificates
    ) {
      return html`<div class="empty">
        No ingresses, HTTPRoutes, certificates, or services found.
      </div>`;
    }

    return html`
      ${this.renderStaleHint()}
      <div class="filters">
        <input
          class="search-input"
          type="text"
          placeholder="Search ingresses, HTTPRoutes, certificates, and services…"
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
          <option value="Services">Services</option>
          ${NETWORK_TYPES.map((t) => html`<option value=${t} ?selected=${t === this._typeFilter}>${t}</option>`)}
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
        // Gateway API is optional: without routes the section only shows when
        // asked for by the filter, or to report an error.
        this._typeFilter === "HTTPRoute" ||
        (this._typeFilter === "all" && (hasHTTPRoutes || this._httprouteError))
          ? html`
              <h2 class="section-title">HTTPRoutes</h2>
              ${
                this._httprouteError
                  ? this._renderInlineError(this._httprouteError)
                  : hasHTTPRoutes
                    ? httprouteClusters.map((cluster) =>
                        this._renderHTTPRouteCluster(cluster),
                      )
                    : html`<div class="empty">No HTTPRoutes found.</div>`
              }
            `
          : nothing
      }
      ${
        // cert-manager is optional too: same rule as the HTTPRoutes section.
        this._typeFilter === "Certificate" ||
        (this._typeFilter === "all" && (hasCertificates || this._certificateError))
          ? html`
              <h2 class="section-title">Certificates</h2>
              ${
                this._certificateError
                  ? this._renderInlineError(this._certificateError)
                  : hasCertificates
                    ? certificateClusters.map((cluster) =>
                        this._renderCertificateCluster(cluster),
                      )
                    : html`<div class="empty">No certificates found.</div>`
              }
            `
          : nothing
      }
      ${
        this._typeFilter !== "Ingress" &&
        this._typeFilter !== "HTTPRoute" &&
        this._typeFilter !== "Certificate"
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

  private _renderHTTPRouteCluster(cluster: ClusterHTTPRoutes) {
    if (!cluster.httproutes.length) return nothing;
    const httproutes = this._getFilteredHTTPRoutes(cluster.httproutes);

    return html`
      <div class="cluster-section">
        ${
          this._httproutes!.clusters.length > 1
            ? html`<div class="cluster-name">${cluster.cluster_name}</div>`
            : nothing
        }
        ${
          httproutes.length === 0
            ? html`<div class="empty">No HTTPRoutes match your search.</div>`
            : this._renderHTTPRoutesTable(httproutes)
        }
      </div>
    `;
  }

  private _renderHTTPRoutesTable(httproutes: HTTPRouteData[]) {
    return html`
      <ha-card>
        <div class="table-wrapper">
          <table class="network-table">
            <thead>
              <tr>
                <th>Name</th>
                <th>Namespace</th>
                <th>URLs</th>
                <th>Gateway</th>
                <th>Backend</th>
                <th>Status</th>
                <th>Age</th>
              </tr>
            </thead>
            <tbody>
              ${httproutes.map(
                (route) => html`
                  <tr>
                    <td>${route.name}</td>
                    <td>${route.namespace}</td>
                    <td>${this._renderUrls(route.urls)}</td>
                    <td>${this._gatewaysOf(route)}</td>
                    <td>${this._backendsOf(route)}</td>
                    <td>${this._renderHTTPRouteStatusBadge(route)}</td>
                    <td>${formatAge(route.creation_timestamp)}</td>
                  </tr>
                `,
              )}
            </tbody>
          </table>
        </div>
      </ha-card>
    `;
  }

  private _renderHTTPRouteStatusBadge(route: HTTPRouteData) {
    return route.accepted && route.resolved_refs
      ? html`<span class="badge badge-ready">Accepted</span>`
      : html`<span class="badge badge-pending">Not Ready</span>`;
  }

  private _renderCertificateCluster(cluster: ClusterCertificates) {
    if (!cluster.certificates.length) return nothing;
    const certificates = this._getFilteredCertificates(cluster.certificates);

    return html`
      <div class="cluster-section">
        ${
          this._certificates!.clusters.length > 1
            ? html`<div class="cluster-name">${cluster.cluster_name}</div>`
            : nothing
        }
        ${
          certificates.length === 0
            ? html`<div class="empty">No certificates match your search.</div>`
            : this._renderCertificatesTable(certificates)
        }
      </div>
    `;
  }

  private _renderCertificatesTable(certificates: CertificateData[]) {
    return html`
      <ha-card>
        <div class="table-wrapper">
          <table class="network-table">
            <thead>
              <tr>
                <th>Name</th>
                <th>Namespace</th>
                <th>DNS Names</th>
                <th>Issuer</th>
                <th>Expires</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              ${certificates.map(
                (cert) => html`
                  <tr>
                    <td>${cert.name}</td>
                    <td>${cert.namespace}</td>
                    <td>
                      ${
                        cert.dns_names.length
                          ? cert.dns_names.map((d) => html`<div>${d}</div>`)
                          : "—"
                      }
                    </td>
                    <td>${cert.issuer_kind}/${cert.issuer_name || "—"}</td>
                    <td>
                      ${
                        cert.not_after
                          ? html`<div>${formatUntil(cert.not_after)}</div>
                              <div class="secondary">
                                ${new Date(cert.not_after).toLocaleString()}
                              </div>`
                          : "—"
                      }
                    </td>
                    <td>${this._renderCertificateStatusBadge(cert)}</td>
                  </tr>
                `,
              )}
            </tbody>
          </table>
        </div>
      </ha-card>
    `;
  }

  private _renderCertificateStatusBadge(cert: CertificateData) {
    const status = certificateStatus(cert);
    return status === "Ready"
      ? html`<span class="badge badge-ready">Ready</span>`
      : html`<span class="badge badge-failed" title=${cert.message ?? ""}
          >${status}</span
        >`;
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
