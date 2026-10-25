import { css } from "lit";
import { themeTokens } from "./styles";

export const dashboardCardStyles = [
  themeTokens,
  css`
    :host {
      display: block;
      box-sizing: border-box;
    }

    ha-card {
      box-sizing: border-box;
      padding: var(--ha-space-4, 16px);
      display: flex;
      flex-direction: column;
      gap: 14px;
      background: var(--unraid-card-bg);
      border: 1px solid var(--unraid-border);
      border-radius: var(--unraid-radius);
      color: var(--unraid-text);
      font-family: var(--ha-card-font-family, inherit);
    }

    :host([embedded]) ha-card {
      border: none;
      box-shadow: none;
      background: transparent;
      padding: 0;
    }

    .icon {
      display: inline-block;
      vertical-align: middle;
      fill: currentColor;
      flex-shrink: 0;
    }

    /* Header */
    .header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 10px;
    }

    .header-main {
      display: flex;
      align-items: center;
      gap: 12px;
      min-width: 0;
    }

    .header-icon {
      width: 40px;
      height: 40px;
      border-radius: 10px;
      background: color-mix(in srgb, var(--unraid-accent) 15%, transparent);
      color: var(--unraid-accent);
      display: grid;
      place-items: center;
      flex-shrink: 0;
    }

    .header-titles {
      display: flex;
      flex-direction: column;
      min-width: 0;
    }

    .header-title {
      font-size: 1.05rem;
      font-weight: 700;
      color: var(--unraid-text);
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
      line-height: 1.25;
    }

    .header-subtitle {
      font-size: 0.78rem;
      color: var(--unraid-subtext);
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }

    .header-actions {
      display: flex;
      align-items: center;
      gap: 8px;
      flex-shrink: 0;
    }

    /* Badges / Chips */
    .badge {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 3px 8px;
      border-radius: 6px;
      font-size: 0.72rem;
      font-weight: 600;
      line-height: 1;
      white-space: nowrap;
    }

    .badge-online {
      background: color-mix(in srgb, var(--unraid-online) 15%, transparent);
      color: var(--unraid-online);
      border: 1px solid color-mix(in srgb, var(--unraid-online) 25%, transparent);
    }

    .badge-warning {
      background: color-mix(in srgb, var(--unraid-warning) 15%, transparent);
      color: var(--unraid-warning);
      border: 1px solid color-mix(in srgb, var(--unraid-warning) 25%, transparent);
    }

    .badge-error {
      background: color-mix(in srgb, var(--unraid-error) 15%, transparent);
      color: var(--unraid-error);
      border: 1px solid color-mix(in srgb, var(--unraid-error) 25%, transparent);
    }

    .badge-standby {
      background: color-mix(in srgb, var(--unraid-standby) 15%, transparent);
      color: var(--unraid-standby);
      border: 1px solid color-mix(in srgb, var(--unraid-standby) 25%, transparent);
    }

    .pulse-dot {
      width: 7px;
      height: 7px;
      border-radius: 50%;
      background: currentColor;
    }

    /* Conic Ring Gauges */
    .rings-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(85px, 1fr));
      gap: 8px;
    }

    .ring-card {
      background: color-mix(in srgb, var(--unraid-text) 3%, transparent);
      border: 1px solid var(--unraid-border);
      border-radius: 10px;
      padding: 10px 6px;
      display: flex;
      flex-direction: column;
      align-items: center;
      text-align: center;
      gap: 6px;
    }

    .ring-card[role="button"]:focus-visible {
      outline: 2px solid var(--unraid-primary);
      outline-offset: 2px;
    }

    .ring-gauge {
      width: 54px;
      height: 54px;
      border-radius: 50%;
      position: relative;
      display: grid;
      place-items: center;
      background: conic-gradient(
        var(--ring-color, var(--unraid-primary)) calc(var(--pct, 0) * 1%),
        color-mix(in srgb, var(--unraid-text) 8%, transparent) 0
      );
      flex-shrink: 0;
    }

    .ring-gauge::after {
      content: "";
      position: absolute;
      inset: 6px;
      border-radius: 50%;
      background: var(--unraid-card-bg);
    }

    .ring-content {
      position: relative;
      z-index: 2;
      font-size: 0.75rem;
      font-weight: 700;
      color: var(--unraid-text);
    }

    .ring-label {
      font-size: 0.72rem;
      font-weight: 600;
      color: var(--unraid-text);
      line-height: 1.1;
    }

    .ring-subtext {
      font-size: 0.68rem;
      color: var(--unraid-subtext);
      line-height: 1.1;
      white-space: nowrap;
    }

    /* Progress Bars */
    .progress-bar {
      width: 100%;
      height: 6px;
      background: color-mix(in srgb, var(--unraid-text) 10%, transparent);
      border-radius: 4px;
      overflow: hidden;
    }

    .progress-fill {
      height: 100%;
      background: var(--fill-color, var(--unraid-accent));
      border-radius: 4px;
      transition: width 0.3s ease;
    }

    /* Lists / Tables */
    .item-list {
      display: flex;
      flex-direction: column;
      gap: 6px;
    }

    .list-row {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 8px 12px;
      border-radius: 8px;
      background: color-mix(in srgb, var(--unraid-text) 3%, transparent);
      border: 1px solid var(--unraid-border);
      gap: 10px;
      font-size: 0.8rem;
      transition: border-color 0.2s ease;
    }

    .list-row:hover {
      border-color: color-mix(in srgb, var(--unraid-accent) 40%, transparent);
    }

    .row-left {
      display: flex;
      align-items: center;
      gap: 10px;
      min-width: 0;
      flex: 1;
    }

    .row-right {
      display: flex;
      align-items: center;
      gap: 10px;
      flex-shrink: 0;
    }

    /* Disk / Storage Item Lists */
    .disk-list {
      display: flex;
      flex-direction: column;
      gap: 6px;
    }

    .disk-row {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 8px 12px;
      border-radius: 8px;
      background: color-mix(in srgb, var(--unraid-text) 3%, transparent);
      border: 1px solid var(--unraid-border);
      gap: 10px;
      font-size: 0.8rem;
      transition: border-color 0.2s ease;
    }

    .disk-row:hover {
      border-color: color-mix(in srgb, var(--unraid-accent) 40%, transparent);
    }

    .disk-main {
      display: flex;
      align-items: center;
      gap: 10px;
      min-width: 0;
      flex: 1;
    }

    .disk-icon {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      width: 28px;
      height: 28px;
      border-radius: 6px;
      flex-shrink: 0;
      background: color-mix(in srgb, var(--unraid-text) 6%, transparent);
      color: var(--unraid-subtext);
    }

    .disk-icon.disk-online {
      background: color-mix(in srgb, var(--unraid-online) 12%, transparent);
      color: var(--unraid-online);
    }

    .disk-icon.disk-standby {
      background: color-mix(in srgb, var(--unraid-standby) 12%, transparent);
      color: var(--unraid-standby);
    }

    .disk-icon.disk-warning {
      background: color-mix(in srgb, var(--unraid-warning) 12%, transparent);
      color: var(--unraid-warning);
    }

    .disk-info {
      display: flex;
      flex-direction: column;
      min-width: 0;
      gap: 2px;
    }

    .disk-name {
      font-weight: 600;
      color: var(--unraid-text);
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }

    .disk-subtext {
      font-size: 0.72rem;
      color: var(--unraid-subtext);
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }

    .disk-meta {
      display: flex;
      align-items: center;
      gap: 10px;
      flex-shrink: 0;
    }

    .disk-temp {
      font-weight: 600;
      font-size: 0.78rem;
      color: var(--unraid-text);
    }

    /* Empty States */
    .empty-state {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      text-align: center;
      padding: 24px 16px;
      gap: 8px;
      color: var(--unraid-subtext);
    }

    .empty-title {
      font-size: 0.86rem;
      font-weight: 600;
      color: var(--unraid-text);
    }

    .empty-subtext {
      font-size: 0.75rem;
      max-width: 320px;
      line-height: 1.3;
    }

    /* Buttons */
    .btn {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 6px;
      padding: 5px 12px;
      border-radius: 8px;
      font-size: 0.78rem;
      font-weight: 600;
      border: 1px solid var(--unraid-border);
      background: color-mix(in srgb, var(--unraid-text) 6%, transparent);
      color: var(--unraid-text);
      cursor: pointer;
      transition: all 0.2s ease;
    }

    .btn:hover {
      background: color-mix(in srgb, var(--unraid-text) 12%, transparent);
    }

    .btn-danger {
      color: var(--error-color, #db4437);
      border-color: var(--error-color, #db4437);
    }

    .btn-primary {
      background: var(--unraid-accent);
      color: white;
      border-color: transparent;
    }

    .btn-primary:hover {
      filter: brightness(1.1);
    }

    .btn-icon {
      padding: 6px;
      border-radius: 6px;
      border: 1px solid transparent;
      background: transparent;
      color: var(--unraid-subtext);
      cursor: pointer;
    }

    .btn-icon:hover {
      background: color-mix(in srgb, var(--unraid-text) 8%, transparent);
      color: var(--unraid-text);
    }

    .btn, .btn-icon, .tab-btn {
      min-height: 44px;
      min-width: 44px;
      box-sizing: border-box;
      font-family: inherit;
    }

    button:focus-visible, [tabindex="0"]:focus-visible {
      outline: 2px solid var(--primary-color, #03a9f4);
      outline-offset: 2px;
    }

    dialog {
      max-width: min(420px, calc(100vw - 64px));
      border: 1px solid var(--unraid-border);
      border-radius: var(--unraid-radius);
      padding: var(--ha-space-6, 24px);
      color: var(--unraid-text);
      background: var(--unraid-card-bg);
    }
    dialog::backdrop { background: rgba(0, 0, 0, 0.5); }
    dialog h2 { margin-block-start: 0; font-size: 1.25rem; }
    .dialog-actions { display: flex; justify-content: flex-end; gap: var(--ha-space-2, 8px); }

    .btn:disabled, .btn-icon:disabled { cursor: default; opacity: 0.5; }

    @media (max-width: 450px) {
      .list-row, .row-left, .row-right { flex-wrap: wrap; }
      .row-left { min-width: 0; }
      .row-right { margin-inline-start: auto; }
    }

    @media (prefers-reduced-motion: reduce) {
      *, *::before, *::after {
        transition: none !important;
        animation: none !important;
      }
    }

    /* Docker Containers Grid View (like Unraid GUI) */
    .container-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(min(100%, 200px), 1fr));
      gap: 8px;
    }

    .container-tile {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 8px 10px;
      border-radius: 8px;
      background: color-mix(in srgb, var(--unraid-text) 4%, transparent);
      border: 1px solid var(--unraid-border);
      gap: 6px;
      transition: all 0.2s ease;
    }

    .container-tile:hover {
      border-color: var(--unraid-accent);
    }

    .tile-name {
      font-size: 0.76rem;
      font-weight: 600;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
      min-width: 0;
    }

    .tile-name.btn {
      min-width: 44px;
      background: transparent;
      border: none;
      padding-inline: 0;
      justify-content: flex-start;
      text-align: start;
      font-size: var(--ha-font-size-s, 14px);
    }


    .status-dot {
      width: 8px;
      height: 8px;
      border-radius: 50%;
      flex-shrink: 0;
    }

    .status-dot.online {
      background: var(--unraid-online);
    }

    .status-dot.offline {
      background: var(--unraid-error);
      border-radius: 2px;
    }

    /* Section divider */
    .divider {
      height: 1px;
      background: var(--unraid-border);
      width: 100%;
      margin: 4px 0;
    }

    /* Details Rows */
    .detail-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
      gap: 8px;
      font-size: 0.75rem;
    }

    .detail-item {
      display: flex;
      flex-direction: column;
      gap: 2px;
    }

    .detail-item[role="button"]:focus-visible {
      outline: 2px solid var(--unraid-primary);
      outline-offset: 2px;
      border-radius: 4px;
    }

    .detail-label {
      color: var(--unraid-subtext);
      font-size: 0.68rem;
    }

    .detail-val {
      font-weight: 600;
      color: var(--unraid-text);
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }

    /* Tab strip for unified dashboard card */
    .tab-strip {
      display: flex;
      gap: 6px;
      overflow-x: auto;
      border-bottom: 1px solid var(--unraid-border);
      padding-bottom: 6px;
    }

    .tab-btn {
      padding: 4px 10px;
      border-radius: 6px;
      font-size: 0.76rem;
      font-weight: 600;
      background: transparent;
      border: none;
      color: var(--unraid-subtext);
      cursor: pointer;
      white-space: nowrap;
      transition: all 0.2s ease;
    }

    .tab-btn:hover {
      color: var(--unraid-text);
      background: color-mix(in srgb, var(--unraid-text) 5%, transparent);
    }

    .tab-btn.active {
      background: color-mix(in srgb, var(--unraid-accent) 15%, transparent);
      color: var(--unraid-accent);
    }
  `,
];
