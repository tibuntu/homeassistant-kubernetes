"""Constants for the Kubernetes integration."""

DOMAIN = "kubernetes"

# Configuration keys
CONF_HOST = "host"
CONF_PORT = "port"
CONF_API_TOKEN = "api_token"
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

# Sensor types
SENSOR_TYPE_PODS = "pods"
SENSOR_TYPE_NODES = "nodes"
SENSOR_TYPE_SERVICES = "services"
SENSOR_TYPE_DEPLOYMENTS = "deployments"

# Binary sensor types
BINARY_SENSOR_TYPE_CLUSTER_HEALTH = "cluster_health"

# Switch types
SWITCH_TYPE_DEPLOYMENT = "deployment"

# Service names
SERVICE_SCALE_DEPLOYMENT = "scale_deployment"
SERVICE_STOP_DEPLOYMENT = "stop_deployment"
SERVICE_START_DEPLOYMENT = "start_deployment"

# Service attributes
ATTR_DEPLOYMENT_NAME = "deployment_name"
ATTR_NAMESPACE = "namespace"
ATTR_REPLICAS = "replicas"
