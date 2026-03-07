import { LitElement, html, css, PropertyValues } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import { loadHaElements } from "./utils/load-ha-elements";
import "./views/k8s-overview";
import "./views/k8s-nodes-table";
import "./views/k8s-pods-table";
import "./views/k8s-workloads";
import "./views/k8s-settings";

type Tab = "overview" | "nodes" | "workloads" | "pods" | "settings";

interface TabDef {
  id: Tab;
  label: string;
  icon: string;
}

@customElement("kubernetes-panel")
export class KubernetesPanel extends LitElement {
  @property({ attribute: false }) public hass!: any;
  @property({ type: Boolean, reflect: true }) public narrow = false;
  @property({ attribute: false }) public route!: any;
  @property({ attribute: false }) public panel!: any;

  @state() private _activeTab: Tab = "overview";

  private _tabs: TabDef[] = [
    { id: "overview", label: "Overview", icon: "mdi:view-dashboard" },
    { id: "nodes", label: "Nodes", icon: "mdi:server" },
    { id: "workloads", label: "Workloads", icon: "mdi:application-cog" },
    { id: "pods", label: "Pods", icon: "mdi:cube-outline" },
    { id: "settings", label: "Settings", icon: "mdi:cog" },
  ];

  protected firstUpdated(_changedProps: PropertyValues): void {
    loadHaElements();
  }

  private _handleTabChange(tab: Tab): void {
    this._activeTab = tab;
  }

  private _toggleSidebar(): void {
    this.dispatchEvent(
      new Event("hass-toggle-menu", { bubbles: true, composed: true }),
    );
  }

  static styles = css`
    :host {
      display: block;
      height: 100%;
      background: var(--primary-background-color);
      color: var(--primary-text-color);
    }

    .toolbar {
      display: flex;
      align-items: center;
      height: 56px;
      padding: 0 16px;
      background: var(--app-header-background-color, var(--primary-color));
      color: var(--app-header-text-color, var(--text-primary-color, #fff));
      font-size: 20px;
      box-sizing: border-box;
    }

    .toolbar h1 {
      margin: 0;
      font-size: 20px;
      font-weight: 400;
      flex: 1;
    }

    .menu-btn {
      display: none;
      cursor: pointer;
      margin-right: 8px;
      --mdc-icon-size: 24px;
    }

    :host([narrow]) .menu-btn {
      display: block;
    }

    .tab-bar {
      display: flex;
      background: var(--primary-background-color);
      border-bottom: 1px solid var(--divider-color);
      overflow-x: auto;
      scrollbar-width: none;
    }

    .tab-bar::-webkit-scrollbar {
      display: none;
    }

    .tab {
      display: flex;
      align-items: center;
      gap: 6px;
      padding: 12px 20px;
      cursor: pointer;
      font-size: 14px;
      color: var(--secondary-text-color);
      border-bottom: 2px solid transparent;
      white-space: nowrap;
      transition:
        color 0.2s,
        border-color 0.2s;
      user-select: none;
      --mdc-icon-size: 20px;
    }

    .tab:hover {
      color: var(--primary-text-color);
    }

    .tab[active] {
      color: var(--primary-color);
      border-bottom-color: var(--primary-color);
    }

    .content {
      padding: 16px;
      overflow-y: auto;
      height: calc(100% - 56px - 49px);
      box-sizing: border-box;
    }

    .coming-soon {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      padding: 64px 16px;
      color: var(--secondary-text-color);
      text-align: center;
      --mdc-icon-size: 48px;
    }

    .coming-soon p {
      margin-top: 16px;
      font-size: 16px;
    }
  `;

  protected render() {
    return html`
      <div class="toolbar">
        <div class="menu-btn" @click=${this._toggleSidebar}>
          <ha-icon icon="mdi:menu"></ha-icon>
        </div>
        <h1>Kubernetes</h1>
      </div>
      <div class="tab-bar">
        ${this._tabs.map(
          (tab) => html`
            <div
              class="tab"
              ?active=${this._activeTab === tab.id}
              @click=${() => this._handleTabChange(tab.id)}
            >
              <ha-icon icon=${tab.icon}></ha-icon>
              <span>${tab.label}</span>
            </div>
          `,
        )}
      </div>
      <div class="content">${this._renderActiveTab()}</div>
    `;
  }

  private _renderActiveTab() {
    switch (this._activeTab) {
      case "overview":
        return html`<k8s-overview .hass=${this.hass}></k8s-overview>`;
      case "nodes":
        return html`<k8s-nodes-table .hass=${this.hass}></k8s-nodes-table>`;
      case "pods":
        return html`<k8s-pods-table .hass=${this.hass}></k8s-pods-table>`;
      case "workloads":
        return html`<k8s-workloads .hass=${this.hass}></k8s-workloads>`;
      case "settings":
        return html`<k8s-settings .hass=${this.hass}></k8s-settings>`;
      default:
        return html`
          <div class="coming-soon">
            <ha-icon icon="mdi:hammer-wrench"></ha-icon>
            <p>This tab is coming in a future release.</p>
          </div>
        `;
    }
  }
}
