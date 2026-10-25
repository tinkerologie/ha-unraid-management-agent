export const SERVER_CARD_TAG = "unraid-management-agent-server-card";
export const SERVER_EDITOR_TAG = "unraid-management-agent-server-card-editor";

export const STORAGE_CARD_TAG = "unraid-management-agent-storage-card";
export const STORAGE_EDITOR_TAG = "unraid-management-agent-storage-card-editor";

export const DOCKER_CARD_TAG = "unraid-management-agent-docker-card";
export const DOCKER_EDITOR_TAG = "unraid-management-agent-docker-card-editor";

export const UPS_CARD_TAG = "unraid-management-agent-ups-card";
export const UPS_EDITOR_TAG = "unraid-management-agent-ups-card-editor";

export const VM_CARD_TAG = "unraid-management-agent-vm-card";
export const VM_EDITOR_TAG = "unraid-management-agent-vm-card-editor";

export const SHARES_CARD_TAG = "unraid-management-agent-shares-card";
export const SHARES_EDITOR_TAG = "unraid-management-agent-shares-card-editor";

export const NETWORK_CARD_TAG = "unraid-management-agent-network-card";
export const NETWORK_EDITOR_TAG = "unraid-management-agent-network-card-editor";

export const ZFS_CARD_TAG = "unraid-management-agent-zfs-card";
export const ZFS_EDITOR_TAG = "unraid-management-agent-zfs-card-editor";

export const FANS_CARD_TAG = "unraid-management-agent-fans-card";
export const FANS_EDITOR_TAG = "unraid-management-agent-fans-card-editor";

export const GPU_CARD_TAG = "unraid-management-agent-gpu-card";
export const GPU_EDITOR_TAG = "unraid-management-agent-gpu-card-editor";

export const NOTIFICATIONS_CARD_TAG = "unraid-management-agent-notifications-card";
export const NOTIFICATIONS_EDITOR_TAG = "unraid-management-agent-notifications-card-editor";

export const MAINTENANCE_CARD_TAG = "unraid-management-agent-maintenance-card";
export const MAINTENANCE_EDITOR_TAG = "unraid-management-agent-maintenance-card-editor";

export const REMOTE_SHARES_CARD_TAG = "unraid-management-agent-remote-shares-card";
export const REMOTE_SHARES_EDITOR_TAG = "unraid-management-agent-remote-shares-card-editor";

export const UNASSIGNED_DEVICES_CARD_TAG = "unraid-management-agent-unassigned-devices-card";
export const UNASSIGNED_DEVICES_EDITOR_TAG = "unraid-management-agent-unassigned-devices-card-editor";

export const DASHBOARD_CARD_TAG = "unraid-management-agent-dashboard-card";
export const DASHBOARD_EDITOR_TAG = "unraid-management-agent-dashboard-card-editor";

export interface CardConfig {
  type: string;
  server?: string;
  name?: string;
  title?: string;
  view_mode?: "grid" | "list";
  show_system_info?: boolean;
  show_motherboard?: boolean;
  show_user_shares?: boolean;
  embedded?: boolean;
  hide_header?: boolean;
  [key: string]: unknown;
}
