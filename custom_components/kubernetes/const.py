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
CONF_DEVICE_GROUPING_MODE = "device_grouping_mode"

# Device grouping modes
DEVICE_GROUPING_MODE_NAMESPACE = "namespace"
DEVICE_GROUPING_MODE_CLUSTER = "cluster"

# Default values
DEFAULT_PORT = 6443
DEFAULT_CLUSTER_NAME = "default"
DEFAULT_NAMESPACE = "default"
DEFAULT_MONITOR_ALL_NAMESPACES = False
DEFAULT_VERIFY_SSL = True
DEFAULT_DEVICE_GROUPING_MODE = DEVICE_GROUPING_MODE_NAMESPACE

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
SENSOR_TYPE_POD = "pod"
SENSOR_TYPE_NODES = "nodes"
SENSOR_TYPE_DEPLOYMENTS = "deployments"
SENSOR_TYPE_STATEFULSETS = "statefulsets"
SENSOR_TYPE_CRONJOBS = "cronjobs"

# Binary sensor types
BINARY_SENSOR_TYPE_CLUSTER_HEALTH = "cluster_health"

# Switch types
SWITCH_TYPE_DEPLOYMENT = "deployment"
SWITCH_TYPE_STATEFULSET = "statefulset"
SWITCH_TYPE_CRONJOB = "cronjob"

# Workload types
WORKLOAD_TYPE_DEPLOYMENT = "Deployment"
WORKLOAD_TYPE_STATEFULSET = "StatefulSet"
WORKLOAD_TYPE_DAEMONSET = "DaemonSet"
WORKLOAD_TYPE_CRONJOB = "CronJob"
WORKLOAD_TYPE_POD = "Pod"

# Service names
SERVICE_SCALE_WORKLOAD = "scale_workload"
SERVICE_START_WORKLOAD = "start_workload"
SERVICE_STOP_WORKLOAD = "stop_workload"

# Service attributes
ATTR_WORKLOAD_NAME = "workload_name"
ATTR_WORKLOAD_NAMES = "workload_names"
ATTR_NAMESPACE = "namespace"
ATTR_REPLICAS = "replicas"
ATTR_JOB_NAME = "job_name"
ATTR_SUSPEND_TIME = "suspend_time"
ATTR_RESUME_TIME = "resume_time"

# Workload attributes
ATTR_WORKLOAD_TYPE = "workload_type"
