# Kubernetes Integration Logging

This document explains the logging system used by the Kubernetes integration and how to troubleshoot common issues.

## Log Levels

The integration uses different log levels to provide appropriate information:

- **DEBUG**: Successful operations and detailed information
- **INFO**: Important successful operations (like scaling deployments)
- **WARNING**: Degraded but working (metrics unavailable, a resource the ServiceAccount may not read, an object that could not be parsed)
- **ERROR**: Problems that need attention

## Log Format

All logs include structured context information:

```
[operation] (cluster=name, host=host:port, namespaces=ns1,ns2): details
```

## Common Error Messages and Solutions

### Authentication Failed (401)

```
aiohttp connection test failed with status: 401
```

**Solutions:**

1. Verify the API token is correct and not expired
2. Check that the service account has the necessary RBAC permissions
3. Ensure the token has access to the specified namespace

A 401 that persists across a poll cycle also raises a **"Reauthentication needed"** notification in Home Assistant, where you can enter a fresh token without reconfiguring the rest of the entry. See [Re-authentication](CONFIGURATION.md#re-authentication).

### Permission Denied (403)

```
Unexpected error during get deployments (cluster=default, host=kubernetes.example.com:6443, namespaces=default): deployments request failed for namespace default with status 403
```

**Solutions:**

1. Check RBAC roles assigned to the service account
2. Verify namespace access permissions
3. Review cluster role bindings

### Resource Not Found (404)

```
Unexpected error during get deployments (cluster=default, host=kubernetes.example.com:6443, namespaces=default): deployments request failed for namespace default with status 404
```

**Solutions:**

1. Verify the namespace exists
2. Check that the resource names are correct
3. Ensure the namespace is accessible

### Network Errors

```
Network error during get deployments (cluster=default, host=kubernetes.example.com:6443, namespaces=default): [error details]
```

**Solutions:**

1. Check network connectivity to the Kubernetes API server
2. Verify firewall rules allow HTTPS traffic to the API server
3. Check DNS resolution for the hostname

### Timeout Errors

```
Timeout during get deployments (cluster=default, host=kubernetes.example.com:6443, namespaces=default). Check network connectivity and API server response time.
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

If you're experiencing authentication issues, verify the token outside Home Assistant with the same request the integration's connection probe makes:

```bash
curl -sS -o /dev/null -w '%{http_code}\n' \
  -H "Authorization: Bearer $TOKEN" \
  https://<host>:<port>/api/v1/
```

- `200` — the token is accepted
- `401` — the token is rejected (the integration raises a reauthentication flow for a persistent 401)
- `403` — the token authenticates but lacks RBAC permissions; see [RBAC.md](RBAC.md)

Add `--cacert <ca.crt>` (or `-k` for a quick test only) when the cluster uses a private CA.

## Log Examples

### Successful Operation

```
DEBUG (MainThread) [custom_components.kubernetes.kubernetes_client] Successfully completed get pods count (cluster=production, host=k8s.example.com:6443, namespaces=default): retrieved 15 pods
```

### Authentication Error

```
ERROR (MainThread) [custom_components.kubernetes.kubernetes_client] aiohttp connection test failed with status: 401
```

### Network Error

```
ERROR (MainThread) [custom_components.kubernetes.kubernetes_client] Network error during get nodes (cluster=production, host=k8s.example.com:6443, namespaces=default): Cannot connect to host k8s.example.com:6443 ssl:default [Connection refused]
```
