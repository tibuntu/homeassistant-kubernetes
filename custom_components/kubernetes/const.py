"""Constants for the Kubernetes integration."""

DOMAIN = "kubernetes"

# Configuration keys
CONF_HOST = "host"
CONF_PORT = "port"
CONF_API_TOKEN = "api_token"  # nosec B105
CONF_CA_CERT = "ca_cert"
CONF_CLUSTER_NAME = "cluster_name"
CONF_NAMESPACE = "namespace"
CONF_MONITOR_ALL_NAMESPACES = "monitor_all_namespaces"
CONF_VERIFY_SSL = "verify_ssl"

# Default values
DEFAULT_PORT = 6443
DEFAULT_CLUSTER_NAME = "default"
DEFAULT_NAMESPACE = "default"
DEFAULT_MONITOR_ALL_NAMESPACES = False
DEFAULT_VERIFY_SSL = True

# Update intervals
DEFAULT_SCAN_INTERVAL = 30
DEFAULT_SWITCH_UPDATE_INTERVAL = 60  # Default polling interval for switches
DEFAULT_SCALE_VERIFICATION_TIMEOUT = 30  # Timeout for verifying scaling operations
DEFAULT_SCALE_COOLDOWN = 10  # Cooldown period after scaling operations

# Polling configuration keys
CONF_SWITCH_UPDATE_INTERVAL = "switch_update_interval"
CONF_SCALE_VERIFICATION_TIMEOUT = "scale_verification_timeout"
CONF_SCALE_COOLDOWN = "scale_cooldown"

# Sensor types
SENSOR_TYPE_PODS = "pods"
SENSOR_TYPE_NODES = "nodes"
SENSOR_TYPE_DEPLOYMENTS = "deployments"
SENSOR_TYPE_STATEFULSETS = "statefulsets"

# Binary sensor types
BINARY_SENSOR_TYPE_CLUSTER_HEALTH = "cluster_health"

# Switch types
SWITCH_TYPE_DEPLOYMENT = "deployment"
SWITCH_TYPE_STATEFULSET = "statefulset"

# Workload types
WORKLOAD_TYPE_DEPLOYMENT = "Deployment"
WORKLOAD_TYPE_STATEFULSET = "StatefulSet"
WORKLOAD_TYPE_DAEMONSET = "DaemonSet"
WORKLOAD_TYPE_CRONJOB = "CronJob"

# Service names
SERVICE_SCALE_DEPLOYMENT = "scale_deployment"
SERVICE_STOP_DEPLOYMENT = "stop_deployment"
SERVICE_START_DEPLOYMENT = "start_deployment"
SERVICE_SCALE_STATEFULSET = "scale_statefulset"
SERVICE_STOP_STATEFULSET = "stop_statefulset"
SERVICE_START_STATEFULSET = "start_statefulset"

# Service attributes
ATTR_DEPLOYMENT_NAME = "deployment_name"
ATTR_STATEFULSET_NAME = "statefulset_name"
ATTR_NAMESPACE = "namespace"
ATTR_REPLICAS = "replicas"

# Multi-selection service attributes
ATTR_DEPLOYMENT_NAMES = "deployment_names"
ATTR_STATEFULSET_NAMES = "statefulset_names"

# Workload attributes
ATTR_WORKLOAD_TYPE = "workload_type"
