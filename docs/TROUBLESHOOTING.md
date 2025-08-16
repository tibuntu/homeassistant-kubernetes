# Troubleshooting Guide

This guide helps you resolve common issues with the Kubernetes integration for Home Assistant.

## Authentication Issues (401 Unauthorized)

### Problem
You see errors like:
```
Failed to stop deployment longhorn-ui
Failed to get deployments: (401)
Reason: Unauthorized
```

### Solution

#### Step 1: Verify RBAC Setup
The integration requires specific RBAC permissions. Run the setup script:

```bash
# Make the script executable
chmod +x scripts/extract_token.sh

# Run the setup script
./scripts/extract_token.sh
```

This script will:
- Create the necessary service account and RBAC resources
- Extract the correct API token
- Provide you with the configuration details

#### Step 2: Manual RBAC Setup (Alternative)
If you prefer to set up RBAC manually:

1. Apply the required manifests:
```bash
kubectl apply -f manifests/serviceaccount.yaml
kubectl apply -f manifests/clusterrole.yaml
kubectl apply -f manifests/clusterrolebinding.yaml
kubectl apply -f manifests/serviceaccount-token-secret.yaml
```

2. Extract the token:
```bash
kubectl get secret homeassistant-monitor-token -n default -o jsonpath='{.data.token}' | base64 -d
```

#### Step 3: Verify Token Permissions
Test if your token has the correct permissions:

```bash
# Replace YOUR_TOKEN with the actual token
curl -H "Authorization: Bearer YOUR_TOKEN" https://YOUR_CLUSTER_HOST:6443/api/v1/

# Test deployment scaling permissions
curl -H "Authorization: Bearer YOUR_TOKEN" https://YOUR_CLUSTER_HOST:6443/apis/apps/v1/namespaces/default/deployments
```

#### Step 4: Update Home Assistant Configuration
1. Go to **Settings** → **Devices & Services**
2. Find your Kubernetes integration and click **Configure**
3. Update the API token with the new token from Step 1 or 2
4. Save the configuration

### Required RBAC Permissions
The service account needs these permissions:

```yaml
# Read permissions
- apiGroups: [""]
  resources: ["pods", "nodes", "namespaces"]
  verbs: ["get", "list", "watch"]

# Deployment permissions (including scaling)
- apiGroups: ["apps"]
  resources: ["deployments", "deployments/scale"]
  verbs: ["get", "list", "watch", "patch", "update"]
```

## Connection Issues

### Problem
Cannot connect to Kubernetes API server.

### Solution

1. **Verify Cluster Accessibility**
   ```bash
   kubectl cluster-info
   ```

2. **Check Network Connectivity**
   ```bash
   # Test if the API server is reachable
   curl -k https://YOUR_CLUSTER_HOST:6443/api/v1/
   ```

3. **Verify SSL Certificate**
   - If using self-signed certificates, set `verify_ssl: false` in the configuration
   - For custom CA certificates, provide the certificate path in the configuration

## Deployment Scaling Issues

### Problem
Deployment scaling operations fail.

### Solution

1. **Check Deployment Exists**
   ```bash
   kubectl get deployments -n NAMESPACE
   ```

2. **Verify Namespace**
   - Ensure the deployment is in the correct namespace
   - Check if you're monitoring all namespaces or a specific one

3. **Check Resource Quotas**
   ```bash
   kubectl describe resourcequota -n NAMESPACE
   ```

## Common Configuration Issues

### Problem
Integration shows incorrect data or no data.

### Solution

1. **Check Namespace Configuration**
   - If `monitor_all_namespaces: false`, ensure the namespace exists
   - If `monitor_all_namespaces: true`, ensure you have cluster-wide permissions

2. **Verify Host Configuration**
   - Remove protocol prefixes (http://, https://) from the host
   - Use only the hostname or IP address

3. **Check Port Configuration**
   - Default Kubernetes API port is 6443
   - For k3s, it might be 6443 or 6443
   - Verify with `kubectl config view`

## Debugging

### Enable Debug Logging
Add this to your `configuration.yaml`:

```yaml
logger:
  default: info
  logs:
    custom_components.kubernetes: debug
```

### Check Home Assistant Logs
Look for detailed error messages in the Home Assistant logs:

```bash
# If running in Docker
docker logs homeassistant

# If running in Kubernetes
kubectl logs -n homeassistant deployment/homeassistant
```

### Test API Endpoints Manually
Use curl to test API endpoints directly:

```bash
# Test basic connectivity
curl -H "Authorization: Bearer YOUR_TOKEN" https://YOUR_CLUSTER_HOST:6443/api/v1/

# Test deployments endpoint
curl -H "Authorization: Bearer YOUR_TOKEN" https://YOUR_CLUSTER_HOST:6443/apis/apps/v1/namespaces/default/deployments

# Test scaling endpoint
curl -X PATCH \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/strategic-merge-patch+json" \
  -d '{"spec":{"replicas":0}}' \
  https://YOUR_CLUSTER_HOST:6443/apis/apps/v1/namespaces/default/deployments/DEPLOYMENT_NAME/scale
```

## Getting Help

If you're still experiencing issues:

1. **Check the logs** with debug logging enabled
2. **Verify your Kubernetes cluster** is working correctly
3. **Test the API endpoints** manually using curl
4. **Create an issue** on the GitHub repository with:
   - Home Assistant version
   - Kubernetes version
   - Error logs
   - Configuration (without sensitive data)

## Security Best Practices

1. **Use Service Accounts**: Always use service accounts instead of user tokens
2. **Principle of Least Privilege**: Only grant necessary permissions
3. **Regular Token Rotation**: Rotate tokens periodically
4. **Network Security**: Use network policies to restrict access
5. **Audit Logging**: Enable audit logging to monitor API access
