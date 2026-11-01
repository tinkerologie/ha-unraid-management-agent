import { html, nothing, type TemplateResult } from "lit";
import {
  NOTIFICATIONS_CARD_TAG,
  NOTIFICATIONS_EDITOR_TAG,
} from "./config";
import { BaseUnraidCard } from "./dashboard-cards-base";
import { UnraidNotificationsCardEditor } from "./dashboard-cards-editor";
import {
  iconTemplate,
  mdiAlertCircle,
  mdiBell,
  mdiCheckCircle,
  mdiInformation,
} from "./icons";
import { registerDashboardCard } from "./register-dashboard-card";

export class UnraidNotificationsCard extends BaseUnraidCard {
  static override editorTag = NOTIFICATIONS_EDITOR_TAG;

  protected override render(): TemplateResult {
    const device = this.getActiveDevice();
    const serverName = this.config.title || device?.name_by_user || device?.name || "Unraid Server";

    const alertsState = this.getEntity("notifications_unread_alert");
    const warningsState = this.getEntity("notifications_unread_warning");
    const infoState = this.getEntity("notifications_unread_info");
    const totalState =
      this.getEntity("notification_count") || this.getEntity("notifications");
    const eventState =
      this.getEntity("notification_event", "event") ||
      this.getEntity("notification", "event");

    const alertCount = Number(alertsState?.state) || 0;
    const warningCount = Number(warningsState?.state) || 0;
    const infoCount = Number(infoState?.state) || 0;
    const totalCount = Number(totalState?.state) || (alertCount + warningCount + infoCount);

    const hasUnread = totalCount > 0;
    const hasTimestamp =
      Boolean(eventState?.state) &&
      eventState?.state !== "unavailable" &&
      eventState?.state !== "unknown";
    const hasContent = Boolean(
      eventState?.attributes?.subject ||
        eventState?.attributes?.description ||
        eventState?.attributes?.message
    );
    const latestEvent =
      hasTimestamp && hasContent ? eventState?.attributes : undefined;

    return html`
      <ha-card>
        ${this.renderHeader(
          serverName,
          "Notifications Center",
          mdiBell,
          html`
            <span class="badge ${alertCount > 0 ? "badge-error" : warningCount > 0 ? "badge-warning" : "badge-online"}">
              <span class="pulse-dot"></span>
              <span>${totalCount} Unread</span>
            </span>
          `
        )}

        <div class="rings-grid">
          <button
            type="button"
            ?disabled=${!(alertsState)}
            class="interactive ring-card"
            @click=${() => alertsState && this.openMoreInfo(alertsState.entity_id)}
            title="Click for Alerts"
          >
            <span data-block
              class="ring-gauge"
              style="--pct: ${alertCount > 0 ? 100 : 0}; --ring-color: var(--unraid-error)"
            >
              <span class="ring-content">${alertCount}</span>
            </span>
            <span class="ring-label">Alerts</span>
            <span class="ring-subtext">Critical Issues</span>
          </button>

          <button
            type="button"
            ?disabled=${!(warningsState)}
            class="interactive ring-card"
            @click=${() => warningsState && this.openMoreInfo(warningsState.entity_id)}
            title="Click for Warnings"
          >
            <span data-block
              class="ring-gauge"
              style="--pct: ${warningCount > 0 ? 100 : 0}; --ring-color: var(--unraid-warning)"
            >
              <span class="ring-content">${warningCount}</span>
            </span>
            <span class="ring-label">Warnings</span>
            <span class="ring-subtext">Action Required</span>
          </button>

          <button
            type="button"
            ?disabled=${!(infoState)}
            class="interactive ring-card"
            @click=${() => infoState && this.openMoreInfo(infoState.entity_id)}
            title="Click for Informational"
          >
            <span data-block
              class="ring-gauge"
              style="--pct: ${infoCount > 0 ? 100 : 0}; --ring-color: var(--unraid-info)"
            >
              <span class="ring-content">${infoCount}</span>
            </span>
            <span class="ring-label">Notices</span>
            <span class="ring-subtext">System Information</span>
          </button>
        </div>

        ${!hasUnread && !latestEvent
          ? html`
              <div class="divider"></div>
              <div class="empty-state">
                ${iconTemplate(mdiCheckCircle, 32)}
                <div class="empty-title">All Clear</div>
                <div class="empty-subtext">There are no unread notifications on this Unraid server.</div>
              </div>
            `
          : latestEvent
          ? html`
              <div class="divider"></div>
              <div class="disk-list">
                <div class="disk-row">
                  <div class="disk-main">
                    <span class="disk-icon ${latestEvent.importance === "alert" ? "disk-warning" : "disk-online"}">
                      ${iconTemplate(
                        latestEvent.importance === "alert"
                          ? mdiAlertCircle
                          : latestEvent.importance === "warning"
                          ? mdiAlertCircle
                          : mdiInformation,
                        18
                      )}
                    </span>
                    <div class="disk-info">
                      <span class="disk-name">${latestEvent.subject || "Latest Notification"}</span>
                      <span class="disk-subtext">${latestEvent.description || latestEvent.message || "No message content"}</span>
                    </div>
                  </div>
                  <div class="disk-meta">
                    <span class="badge ${latestEvent.importance === "alert" ? "badge-error" : latestEvent.importance === "warning" ? "badge-warning" : "badge-online"}">
                      ${latestEvent.importance || "Info"}
                    </span>
                  </div>
                </div>
              </div>
            `
          : nothing}
      </ha-card>
    `;
  }
}

registerDashboardCard({
  tag: NOTIFICATIONS_CARD_TAG,
  editorTag: NOTIFICATIONS_EDITOR_TAG,
  card: UnraidNotificationsCard,
  editor: UnraidNotificationsCardEditor,
  name: "Unraid Notifications Card",
  description: "View Unraid notification counts, severity alerts, and latest messages",
});
