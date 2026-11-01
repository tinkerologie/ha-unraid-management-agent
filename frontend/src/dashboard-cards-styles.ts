import { css } from "lit";
import { themeTokens } from "./styles";

export const dashboardCardStyles = [
  themeTokens,
  css`
    :host {
      display: block;
      box-sizing: border-box;
      font-family: var(--ha-card-font-family, var(--ha-font-family-body, inherit));
      font-size: var(--ha-font-size-m, 14px);
    }

    *,
    *::before,
    *::after {
      box-sizing: border-box;
    }

    button,
    input,
    select {
      font: inherit;
    }

    /* Controls that replaced clickable rows and gauges. Zero specificity, so
       each element's own class still sets its look. */
    :where(.interactive) {
      appearance: none;
      inline-size: 100%;
      min-block-size: 40px;
      padding: 0;
      border: none;
      background: transparent;
      color: inherit;
      text-align: start;
      cursor: pointer;
      touch-action: manipulation;
    }

    :where(.interactive:disabled) {
      color: inherit;
      cursor: default;
    }

    :where(.interactive [data-block]) {
      display: block;
      min-width: 0;
    }

    .sr-only {
      position: absolute;
      inline-size: 1px;
      block-size: 1px;
      overflow: hidden;
      clip-path: inset(50%);
      white-space: nowrap;
    }

    ha-card {
      box-sizing: border-box;
      padding: var(--ha-space-4, 16px);
      background: var(--unraid-card-bg);
      border: var(--ha-card-border-width, 1px) solid var(--unraid-border);
      border-radius: var(--unraid-radius);
      color: var(--unraid-text);
    }

    /* Keep containment inside the card so Sections can size the host normally. */
    .uma-card-content {
      container: unraid-card / inline-size;
      display: flex;
      flex-direction: column;
      gap: var(--ha-space-3, 12px);
      min-inline-size: 0;
    }

    .ltr-value {
      direction: ltr;
      unicode-bidi: isolate;
    }

    .vm-labels {
      display: flex;
      flex-direction: column;
      min-inline-size: 0;
    }

    .entity-name {
      min-inline-size: 0;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
      font-weight: var(--ha-font-weight-bold, 600);
      font-size: var(--ha-font-size-m, 14px);
    }

    .gpu-header, .gpu-name {
      display: flex;
      align-items: center;
      gap: var(--ha-space-2, 8px);
      min-inline-size: 0;
    }

    .gpu-header {
      justify-content: space-between;
      margin-block-end: var(--ha-space-2, 8px);
      inline-size: 100%;
    }

    .gpu-name { flex: 1; }
    .gpu-driver { white-space: normal; overflow-wrap: anywhere; }

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
      flex-wrap: wrap;
      justify-content: space-between;
      gap: var(--ha-space-2, 8px);
    }

    .header-main {
      display: flex;
      flex: 1 1 auto;
      align-items: center;
      gap: var(--ha-space-3, 12px);
      min-width: 0;
    }

    .header-icon {
      width: 40px;
      height: 40px;
      border-radius: var(--ha-border-radius-lg, 12px);
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
      font-size: var(--ha-font-size-l, 16px);
      font-weight: var(--ha-font-weight-bold, 700);
      color: var(--unraid-text);
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
      line-height: 1.25;
    }

    .header-subtitle {
      font-size: var(--ha-font-size-s, 12px);
      color: var(--unraid-subtext);
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }

    .header-actions {
      display: flex;
      align-items: center;
      gap: var(--ha-space-2, 8px);
      flex-shrink: 0;
    }

    /* Badges / Chips */
    .badge {
      display: inline-flex;
      align-items: center;
      gap: var(--ha-space-2, 8px);
      padding: 3px var(--ha-space-2, 8px);
      border-radius: var(--ha-border-radius-md, 8px);
      font-size: var(--ha-font-size-s, 12px);
      font-weight: var(--ha-font-weight-bold, 600);
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
      gap: var(--ha-space-2, 8px);
    }

    .ups-rings { grid-template-columns: repeat(2, minmax(0, 1fr)); }

    .ring-card {
      background: color-mix(in srgb, var(--unraid-text) 3%, transparent);
      border: 1px solid var(--unraid-border);
      border-radius: var(--ha-border-radius-lg, 12px);
      padding: var(--ha-space-2, 8px) var(--ha-space-2, 8px);
      display: flex;
      flex-direction: column;
      align-items: center;
      text-align: center;
      gap: var(--ha-space-2, 8px);
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
      font-size: var(--ha-font-size-s, 12px);
      font-weight: var(--ha-font-weight-bold, 700);
      color: var(--unraid-text);
    }

    .ring-label {
      font-size: var(--ha-font-size-s, 12px);
      font-weight: var(--ha-font-weight-bold, 600);
      color: var(--unraid-text);
      line-height: 1.1;
    }

    .ring-subtext {
      font-size: var(--ha-font-size-s, 12px);
      color: var(--unraid-subtext);
      line-height: 1.1;
      overflow-wrap: anywhere;
    }

    /* Progress Bars */
    .progress-bar {
      width: 100%;
      height: 6px;
      background: color-mix(in srgb, var(--unraid-text) 10%, transparent);
      border-radius: var(--ha-border-radius-sm, 4px);
      overflow: hidden;
    }

    .progress-fill {
      height: 100%;
      background: var(--fill-color, var(--unraid-accent));
      border-radius: var(--ha-border-radius-sm, 4px);
      transition: width 0.3s ease;
    }

    /* Lists / Tables */
    .item-list {
      display: flex;
      flex-direction: column;
      gap: var(--ha-space-2, 8px);
    }

    .list-row {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: var(--ha-space-2, 8px) var(--ha-space-3, 12px);
      border-radius: var(--ha-border-radius-md, 8px);
      background: color-mix(in srgb, var(--unraid-text) 3%, transparent);
      border: 1px solid var(--unraid-border);
      gap: var(--ha-space-2, 8px);
      font-size: var(--ha-font-size-s, 12px);
      transition: border-color 0.2s ease;
    }

    .list-row:hover {
      border-color: color-mix(in srgb, var(--unraid-accent) 40%, transparent);
    }

    .row-left {
      display: flex;
      align-items: center;
      gap: var(--ha-space-2, 8px);
      min-width: 0;
      flex: 1;
    }

    .row-right {
      display: flex;
      align-items: center;
      gap: var(--ha-space-2, 8px);
      flex-shrink: 0;
    }

    /* Disk / Storage Item Lists */
    .disk-list {
      display: flex;
      flex-direction: column;
      gap: var(--ha-space-2, 8px);
    }

    .disk-row {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: var(--ha-space-2, 8px) var(--ha-space-3, 12px);
      border-radius: var(--ha-border-radius-md, 8px);
      background: color-mix(in srgb, var(--unraid-text) 3%, transparent);
      border: 1px solid var(--unraid-border);
      gap: var(--ha-space-2, 8px);
      font-size: var(--ha-font-size-s, 12px);
      transition: border-color 0.2s ease;
    }

    .disk-row:hover {
      border-color: color-mix(in srgb, var(--unraid-accent) 40%, transparent);
    }

    .disk-main {
      display: flex;
      align-items: center;
      gap: var(--ha-space-2, 8px);
      min-width: 0;
      flex: 1;
    }

    .disk-icon {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      width: 28px;
      height: 28px;
      border-radius: var(--ha-border-radius-md, 8px);
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
      font-weight: var(--ha-font-weight-bold, 600);
      color: var(--unraid-text);
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }

    .disk-subtext {
      font-size: var(--ha-font-size-s, 12px);
      color: var(--unraid-subtext);
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }

    .disk-meta {
      display: flex;
      align-items: center;
      gap: var(--ha-space-2, 8px);
      flex-shrink: 0;
    }

    .disk-temp {
      font-weight: var(--ha-font-weight-bold, 600);
      font-size: var(--ha-font-size-s, 12px);
      color: var(--unraid-text);
    }

    /* Empty States */
    .empty-state {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      text-align: center;
      padding: var(--ha-space-6, 24px) var(--ha-space-4, 16px);
      gap: var(--ha-space-2, 8px);
      color: var(--unraid-subtext);
    }

    .empty-title {
      font-size: var(--ha-font-size-m, 14px);
      font-weight: var(--ha-font-weight-bold, 600);
      color: var(--unraid-text);
    }

    .empty-subtext {
      font-size: var(--ha-font-size-s, 12px);
      max-width: 320px;
      line-height: 1.3;
    }

    /* Buttons */
    .btn {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: var(--ha-space-2, 8px);
      padding: var(--ha-space-1, 4px) var(--ha-space-3, 12px);
      border-radius: var(--ha-border-radius-md, 8px);
      font-size: var(--ha-font-size-s, 12px);
      font-weight: var(--ha-font-weight-bold, 600);
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
      color: var(--unraid-error);
      border-color: var(--unraid-error);
    }

    .btn-primary {
      background: var(--unraid-accent);
      color: var(--text-primary-color, #fff);
      border-color: transparent;
    }

    .btn-primary:hover {
      filter: brightness(1.1);
    }

    .btn-icon {
      padding: var(--ha-space-2, 8px);
      border-radius: var(--ha-border-radius-md, 8px);
      border: 1px solid transparent;
      background: transparent;
      color: var(--unraid-subtext);
      cursor: pointer;
    }

    .btn-icon:hover {
      background: color-mix(in srgb, var(--unraid-text) 8%, transparent);
      color: var(--unraid-text);
    }

    .btn, .tab-btn {
      min-block-size: 44px;
      min-inline-size: 44px;
    }

    .btn-icon {
      display: inline-grid;
      place-items: center;
      min-block-size: 48px;
      min-inline-size: 48px;
    }

    :where(button, a, input, select, [tabindex]):focus-visible {
      outline: 2px solid var(--unraid-focus);
      outline-offset: 2px;
    }

    button.badge {
      min-block-size: 44px;
    }

    dialog {
      max-width: min(420px, calc(100vw - 64px));
      border: 1px solid var(--unraid-border);
      border-radius: var(--unraid-radius);
      padding: var(--ha-space-6, 24px);
      color: var(--unraid-text);
      background: var(--unraid-card-bg);
    }
    dialog::backdrop { background: var(--mdc-dialog-scrim-color, rgba(0, 0, 0, 0.32)); }
    dialog h2 { margin-block-start: 0; font-size: var(--ha-font-size-xl, 20px); }
    .dialog-actions { display: flex; justify-content: flex-end; gap: var(--ha-space-2, 8px); }

    .btn:disabled, .btn-icon:disabled { cursor: default; opacity: 0.5; }

    @container unraid-card (max-width: 450px) {
      .list-row, .disk-row, .row-left, .row-right, .disk-meta, .container-tile { flex-wrap: wrap; }
      .row-left { min-width: 0; flex-basis: 100%; }
      .row-right, .disk-meta { margin-inline-start: auto; }
      .network-row, .network-row [data-block] { flex-wrap: wrap; }
      .network-row span { min-inline-size: 0; flex-wrap: wrap; }
      .network-row .ltr-value { overflow-wrap: anywhere; }
    }

    @container unraid-card (max-width: 320px) {
      .header { flex-wrap: wrap; }
      .header-main { flex-basis: 100%; }
      .header-actions { flex-wrap: wrap; min-inline-size: 0; max-inline-size: 100%; }
      .header-actions .badge { white-space: normal; overflow-wrap: anywhere; }
      .ring-subtext {
        max-inline-size: 100%;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
      }
      .ups-rings { grid-template-columns: minmax(0, 1fr); }
      .gpu-header { flex-wrap: wrap; }
      .gpu-name { flex-basis: 100%; }
      .gpu-driver { max-inline-size: 100%; }
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
      gap: var(--ha-space-2, 8px);
    }

    .container-tile {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: var(--ha-space-2, 8px) var(--ha-space-2, 8px);
      border-radius: var(--ha-border-radius-md, 8px);
      background: color-mix(in srgb, var(--unraid-text) 4%, transparent);
      border: 1px solid var(--unraid-border);
      gap: var(--ha-space-2, 8px);
      transition: all 0.2s ease;
    }

    .container-tile:hover {
      border-color: var(--unraid-accent);
    }

    .tile-name {
      font-size: var(--ha-font-size-s, 12px);
      font-weight: var(--ha-font-weight-bold, 600);
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
      margin-block: var(--ha-space-1, 4px);
    }

    /* Details Rows */
    .detail-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
      gap: var(--ha-space-2, 8px);
      font-size: var(--ha-font-size-s, 12px);
    }

    .detail-item {
      display: flex;
      flex-direction: column;
      gap: 2px;
    }

    .detail-label {
      color: var(--unraid-subtext);
      font-size: var(--ha-font-size-s, 12px);
    }

    .detail-val {
      font-weight: var(--ha-font-weight-bold, 600);
      color: var(--unraid-text);
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }

    /* Tab strip for unified dashboard card */
    .tab-strip {
      display: flex;
      gap: var(--ha-space-2, 8px);
      overflow-x: auto;
      scrollbar-width: thin;
      border-block-end: 1px solid var(--unraid-border);
      padding-block-end: var(--ha-space-2, 8px);
    }

    .tab-btn {
      flex-shrink: 0;
      white-space: nowrap;
      padding: var(--ha-space-1, 4px) var(--ha-space-2, 8px);
      border-radius: var(--ha-border-radius-md, 8px);
      font-size: var(--ha-font-size-s, 12px);
      font-weight: var(--ha-font-weight-bold, 600);
      background: transparent;
      border: none;
      color: var(--unraid-subtext);
      cursor: pointer;
      white-space: nowrap;
      display: inline-flex;
      align-items: center;
      gap: var(--ha-space-1, 4px);
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
