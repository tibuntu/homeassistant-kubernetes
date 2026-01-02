# Entity Management

This document explains how the Kubernetes integration manages entities and handles automatic cleanup of orphaned entities.

## Overview

The Kubernetes integration automatically manages Home Assistant entities and devices based on the current state of your Kubernetes cluster. This includes:

- **Automatic Entity Cleanup**: Removing entities for deleted deployments/statefulsets/pods/nodes
- **Automatic Device Cleanup**: Removing namespace devices when namespaces are deleted
- **Dynamic Entity Discovery**: Adding entities for newly created deployments/statefulsets/pods/nodes
- **Dynamic Device Creation**: Creating namespace devices when new namespaces are discovered
- **Real-time Synchronization**: Keeping Home Assistant entities in sync with Kubernetes resources

## Automatic Entity Cleanup

### Problem Addressed

When deployments or statefulsets are deleted from your Kubernetes cluster, their corresponding entities in Home Assistant would previously remain with warnings like:

> "This entity is no longer being provided by the kubernetes integration. If the entity is no longer in use, delete it in settings."

### Solution

The integration now automatically removes orphaned entities during each polling cycle (default: every 60 seconds).

### How It Works

1. **During Each Poll Cycle**:
   - The coordinator fetches current deployments and statefulsets from Kubernetes
   - Compares the current resources against existing Home Assistant entities
   - Identifies entities that no longer have corresponding Kubernetes resources
   - Automatically removes orphaned entities from the entity registry

2. **Entity Identification**:
   - Uses unique IDs in the format: `{config_entry_id}_{resource_name}_{resource_type}`
   - Supports complex resource names containing underscores
   - Handles both deployments and statefulsets

3. **Cleanup Process**:
   - Scans the entity registry for entities belonging to this integration
   - Parses unique IDs to determine resource name and type
   - Removes entities whose corresponding Kubernetes resources no longer exist
   - Removes namespace devices when namespaces no longer contain any resources

### Logging

The cleanup process provides detailed logging:

```
[INFO] Deployment my-app no longer exists, marking entity for removal
[INFO] Removing orphaned entity: switch.my_app_deployment
[INFO] Removed 1 orphaned entities
```

## Dynamic Entity Discovery

### Automatic Detection

The integration automatically detects new deployments and statefulsets created in your cluster and adds corresponding entities to Home Assistant.

### How It Works

1. **Resource Discovery**:
   - During each polling cycle, the coordinator compares current resources against existing entities
   - Identifies new resources that don't have corresponding entities
   - Creates new entities for discovered resources

2. **Entity Creation**:
   - New switch entities are automatically created for deployments and statefulsets
   - Entities are added with proper unique IDs and configuration
   - No restart required - entities appear immediately after the next poll

### Example

If you create a new deployment called `web-server` in your cluster:

1. The next polling cycle will detect the new deployment
2. A new switch entity `switch.web_server_deployment` will be automatically created
3. The entity will be immediately available in Home Assistant

## Configuration

### Polling Interval

The cleanup and discovery frequency is controlled by the **Switch Update Interval** setting (default: 60 seconds).

To adjust the interval:

1. Go to **Settings → Devices & Services**
2. Find your Kubernetes integration
3. Click **Configure**
4. Adjust the **Switch Update Interval** value

### Considerations

- **Lower intervals** (e.g., 30 seconds) provide faster cleanup/discovery but increase API load
- **Higher intervals** (e.g., 120 seconds) reduce API load but delay cleanup/discovery
- The default 60 seconds provides a good balance for most use cases

## Entity Types Supported

The automatic management currently supports:

- **Switch Entities**: For deployments, statefulsets, and cronjobs
- **Sensor Entities**: For pods, nodes, and cluster-wide metrics
- **Binary Sensor Entities**: For cluster health monitoring

## Device Management

### Namespace Device Cleanup

The integration automatically manages namespace devices:

- **Automatic Creation**: Namespace devices are created when the first entity in a namespace is discovered
- **Automatic Cleanup**: Namespace devices are removed when a namespace no longer contains any resources
- **Parent Relationship**: Namespace devices are linked to the cluster device as their parent

### Cluster Device

The cluster device is created when the integration is first set up and persists for the lifetime of the integration. It contains:

- All cluster-level count sensors
- Individual node sensors
- Cluster health binary sensor

## Troubleshooting

### Orphaned Entities Not Being Cleaned Up

1. **Check Logs**: Look for cleanup-related log messages during polling cycles
2. **Verify Polling**: Ensure the integration is actively polling (check last update timestamps)
3. **Unique ID Format**: Entities with non-standard unique IDs may not be cleaned up

### New Resources Not Being Discovered

1. **Check Namespace**: Ensure new resources are in the monitored namespace(s)
2. **RBAC Permissions**: Verify the service account has permissions to list the resources
3. **Polling Interval**: Wait for the next polling cycle to complete

### Manual Cleanup

If automatic cleanup isn't working for specific entities, you can manually remove them:

1. Go to **Settings → Devices & Services → Entities**
2. Search for the orphaned entity
3. Click the entity and select **Delete**

## API Impact

The automatic entity management adds minimal overhead to the existing polling process:

- **Entity Registry Queries**: Lightweight queries to the local entity registry
- **No Additional API Calls**: Uses existing Kubernetes API data
- **Efficient Processing**: Only processes entities belonging to this integration

## Best Practices

1. **Monitor Logs**: Keep an eye on cleanup logs to understand what entities are being managed
2. **Appropriate Polling**: Set polling intervals based on your cluster's change frequency
3. **RBAC Review**: Ensure service account permissions are sufficient for resource discovery
4. **Backup Entity Registry**: Consider backing up your entity registry before major cluster changes

## Version History

- **v1.1.0**: Added automatic entity cleanup and dynamic discovery
- **v1.0.0**: Initial release with manual entity management
