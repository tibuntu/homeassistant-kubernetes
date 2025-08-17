# Kubernetes Integration Logging

This document explains the logging system used by the Kubernetes integration and how to troubleshoot common issues.

## Log Levels

The integration uses different log levels to provide appropriate information:

- **DEBUG**: Successful operations and detailed information
- **INFO**: Important successful operations (like scaling deployments)
- **ERROR**: Problems that need attention

## Error Deduplication

To reduce log noise, authentication errors (401) are deduplicated:

- The first authentication error is logged as ERROR with full details
- Subsequent authentication errors within 5 minutes are logged as DEBUG
- This prevents log spam while still providing visibility into authentication issues

## Log Format

All logs include structured context information:

```
[operation] (cluster=name, host=host:port, namespace=namespace): details
```

## Common Error Messages and Solutions

### Authentication Failed (401)

```
Authentication failed for get deployments (cluster=default, host=kubernetes.example.com:6443, namespace=default). Check API token and RBAC permissions.
```

**Solutions:**

1. Verify the API token is correct and not expired
2. Check that the service account has the necessary RBAC permissions
3. Ensure the token has access to the specified namespace

### Permission Denied (403)

```
Permission denied for get deployments (cluster=default, host=kubernetes.example.com:6443, namespace=default). Check RBAC roles and namespace access.
```

**Solutions:**

1. Check RBAC roles assigned to the service account
2. Verify namespace access permissions
3. Review cluster role bindings

### Resource Not Found (404)

```
Resource not found for get deployments (cluster=default, host=kubernetes.example.com:6443, namespace=default). Check namespace and resource names.
```

**Solutions:**

1. Verify the namespace exists
2. Check that the resource names are correct
3. Ensure the namespace is accessible

### Network Errors

```
Network error during get deployments (cluster=default, host=kubernetes.example.com:6443, namespace=default): [error details]
```

**Solutions:**

1. Check network connectivity to the Kubernetes API server
2. Verify firewall rules allow HTTPS traffic to the API server
3. Check DNS resolution for the hostname

### Timeout Errors

```
Timeout during get deployments (cluster=default, host=kubernetes.example.com:6443, namespace=default). Check network connectivity and API server response time.
```

**Solutions:**

1. Check network latency to the Kubernetes cluster
2. Verify the API server is not overloaded
3. Consider increasing timeout values if needed

## Enabling Debug Logging

To see detailed debug information, add this to your `configuration.yaml`:

```yaml
logger:
  default: info
  logs:
    custom_components.kubernetes: debug
```

## Troubleshooting Steps

1. **Check Connection**: Look for "Successfully connected to Kubernetes API" messages
2. **Verify Permissions**: Check for 401/403 errors and review RBAC configuration
3. **Network Issues**: Look for timeout or network error messages
4. **Resource Access**: Verify namespace and resource existence for 404 errors

## Authentication Testing

If you're experiencing authentication issues, you can test the authentication directly:

```python
# In a Python script or Home Assistant developer tools
client = KubernetesClient(config_data)
auth_status = await client.test_authentication()
print(auth_status)
```

This will return detailed information about:

- Whether authentication succeeded
- Which method was used (kubernetes_client or aiohttp_fallback)
- Specific error details if authentication failed

## Log Examples

### Successful Operation

```
DEBUG (MainThread) [custom_components.kubernetes.kubernetes_client] Successfully completed get pods count (cluster=production, host=k8s.example.com:6443, namespace=default): found 15 pods
```

### Authentication Error

```
ERROR (MainThread) [custom_components.kubernetes.kubernetes_client] Authentication failed for get deployments (cluster=production, host=k8s.example.com:6443, namespace=default). Check API token and RBAC permissions.
```

### Network Error

```
ERROR (MainThread) [custom_components.kubernetes.kubernetes_client] Network error during get nodes count (cluster=production, host=k8s.example.com:6443, namespace=default): Cannot connect to host k8s.example.com:6443 ssl:default [Connection refused]
```
