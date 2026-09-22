import { css } from "lit";

/**
 * Loading spinner, full-page error card with Retry, and the centred empty
 * message rendered by `K8sDataView.renderState()`. Every view composes this.
 */
export const stateStyles = css`
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
`;

/** Filter bar: search input, `<select class="filter-select">`, and filter chips. */
export const filterStyles = css`
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
`;

/**
 * Status pills. Variants are grouped by colour; the class names are the ones
 * the views already render, so markup does not change.
 */
export const badgeStyles = css`
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

  .badge-healthy,
  .badge-ready,
  .badge-running,
  .badge-complete,
  .badge-tls,
  .badge-type-loadbalancer {
    background: rgba(var(--rgb-success-color, 76, 175, 80), 0.15);
    color: var(--success-color, #4caf50);
  }

  .badge-unhealthy,
  .badge-not-ready,
  .badge-failed {
    background: rgba(var(--rgb-error-color, 244, 67, 54), 0.15);
    color: var(--error-color, #f44336);
  }

  .badge-unschedulable,
  .badge-condition,
  .badge-pending,
  .badge-degraded,
  .badge-plain,
  .badge-type-externalname {
    background: rgba(var(--rgb-warning-color, 255, 152, 0), 0.15);
    color: var(--warning-color, #ff9800);
  }

  .badge-unknown,
  .badge-stopped,
  .badge-suspended {
    background: rgba(var(--rgb-disabled-color, 158, 158, 158), 0.15);
    color: var(--disabled-color, #9e9e9e);
  }

  .badge-succeeded,
  .badge-active {
    background: rgba(var(--rgb-info-color, 33, 150, 243), 0.15);
    color: var(--info-color, #2196f3);
  }
`;

/** Modal confirmation dialog (delete pod / delete job / scale). */
export const dialogStyles = css`
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

  .confirm-dialog .confirm-ref {
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
`;

/** Horizontal-scroll wrapper for data tables inside an `<ha-card>`. */
export const tableStyles = css`
  .table-wrapper {
    overflow-x: auto;
  }
`;
