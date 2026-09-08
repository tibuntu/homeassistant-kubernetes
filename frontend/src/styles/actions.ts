import { css } from "lit";

/**
 * Shared styles for the small round action buttons (start/stop/restart/…)
 * and the dismissible error banner shown after a failed action.
 * Used by the Workloads and Nodes views.
 */
export const actionStyles = css`
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

  .action-btn.stop:hover,
  .action-btn.delete:hover {
    background: rgba(var(--rgb-error-color, 244, 67, 54), 0.1);
    color: var(--error-color, #f44336);
  }

  .action-btn.start:hover,
  .action-btn.uncordon:hover {
    background: rgba(var(--rgb-success-color, 76, 175, 80), 0.1);
    color: var(--success-color, #4caf50);
  }

  .action-btn.restart:hover,
  .action-btn.suspend:hover,
  .action-btn.cordon:hover {
    background: rgba(var(--rgb-warning-color, 255, 152, 0), 0.1);
    color: var(--warning-color, #ff9800);
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
`;
