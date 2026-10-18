"""Constants for the Unraid Management Agent integration."""

from __future__ import annotations

from typing import Final

# Integration domain
DOMAIN: Final = "unraid_management_agent"

# Configuration keys
CONF_ENABLE_WEBSOCKET: Final = "enable_websocket"
CONF_ENABLE_FAN_CONTROL: Final = "enable_fan_control"
CONF_ENABLE_CONTAINER_DEVICES: Final = "enable_container_devices"
CONF_ENABLE_CONTAINER_UPDATES: Final = "enable_container_updates"
CONF_READ_ONLY: Final = "read_only"
CONF_CPU_TEMPERATURE_SOURCE: Final = "cpu_temperature_source"
CONF_ENABLE_VM_DEVICES: Final = "enable_vm_devices"
CONF_ENABLE_GPU_DEVICES: Final = "enable_gpu_devices"
CONF_ENABLE_HWMON_DEVICES: Final = "enable_hwmon_devices"
CONF_ENABLE_ZFS_POOL_DEVICES: Final = "enable_zfs_pool_devices"
CONF_ENABLE_NIC_DEVICES: Final = "enable_nic_devices"

# Default values
DEFAULT_PORT: Final = 8043
DEFAULT_ENABLE_WEBSOCKET: Final = True
DEFAULT_ENABLE_FAN_CONTROL: Final = True
DEFAULT_ENABLE_CONTAINER_DEVICES: Final = False
DEFAULT_ENABLE_CONTAINER_UPDATES: Final = False
DEFAULT_READ_ONLY: Final = False
# "auto" uses the agent's CPU temperature (cpu_temp_celsius); any other value
# is the key of the hwmon temperature channel to show instead (issue #195)
CPU_TEMPERATURE_SOURCE_AUTO: Final = "auto"
DEFAULT_CPU_TEMPERATURE_SOURCE: Final = CPU_TEMPERATURE_SOURCE_AUTO
DEFAULT_ENABLE_VM_DEVICES: Final = False
DEFAULT_ENABLE_GPU_DEVICES: Final = False
DEFAULT_ENABLE_HWMON_DEVICES: Final = False
DEFAULT_ENABLE_ZFS_POOL_DEVICES: Final = False
DEFAULT_ENABLE_NIC_DEVICES: Final = False

# Fixed update interval following Home Assistant best practices
# https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/appropriate-polling/
# 30 seconds is appropriate for local network polling with WebSocket as primary update mechanism
# Users who need custom intervals can use HA's built-in custom polling via automations
UPDATE_INTERVAL: Final = 30

# Device info
MANUFACTURER: Final = "Lime Technology"

# Attributes used in sensor.py
ATTR_CPU_MODEL: Final = "cpu_model"
ATTR_CPU_CORES: Final = "cpu_cores"
ATTR_CPU_THREADS: Final = "cpu_threads"
ATTR_RAM_TOTAL: Final = "ram_total"
ATTR_SERVER_MODEL: Final = "server_model"
ATTR_ARRAY_STATE: Final = "array_state"
ATTR_NUM_DISKS: Final = "num_disks"
ATTR_NUM_DATA_DISKS: Final = "num_data_disks"
ATTR_NUM_PARITY_DISKS: Final = "num_parity_disks"
ATTR_GPU_NAME: Final = "gpu_name"
ATTR_GPU_DRIVER_VERSION: Final = "gpu_driver_version"
ATTR_NETWORK_MAC: Final = "network_mac"
ATTR_NETWORK_IP: Final = "network_ip"
ATTR_NETWORK_SPEED: Final = "network_speed"
ATTR_UPS_STATUS: Final = "ups_status"
ATTR_UPS_MODEL: Final = "ups_model"

# Attributes used in binary_sensor.py
ATTR_PARITY_CHECK_STATUS: Final = "parity_check_status"

# Attributes used in switch.py
ATTR_CONTAINER_IMAGE: Final = "container_image"
ATTR_CONTAINER_PORTS: Final = "container_ports"
ATTR_VM_VCPUS: Final = "vm_vcpus"
ATTR_VM_MEMORY: Final = "vm_memory"

# Error messages used in config_flow.py
ERROR_CANNOT_CONNECT: Final = "cannot_connect"
ERROR_UNKNOWN: Final = "unknown"
ERROR_INVALID_AUTH: Final = "invalid_auth"
ERROR_TIMEOUT: Final = "timeout"
