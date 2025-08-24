# CronJob Management

The Kubernetes integration provides comprehensive support for monitoring and managing CronJobs in your Kubernetes cluster.

## Overview

CronJobs are Kubernetes resources that run jobs on a time-based schedule. This integration allows you to:

- **Monitor CronJob Count**: Track the total number of CronJobs in your cluster
- **Control CronJob Suspension**: Enable/disable CronJobs using switches
- **Trigger CronJobs Manually**: Execute CronJobs on-demand using service calls
- **Monitor CronJob Status**: View schedule, suspension status, and active job counts

## Entities

### CronJobs Count Sensor

A sensor that displays the total number of CronJobs in your cluster or namespace.

**Entity ID**: `sensor.kubernetes_cronjobs_count`

**Attributes**:
- `unit_of_measurement`: "cronjobs"
- `state_class`: "measurement"

**Example State**: `3` (indicating 3 CronJobs exist)

### CronJob Switches

Individual switches for each CronJob that control the suspension state.

**Entity ID**: `switch.{cronjob_name}`

**Switch Behavior**:
- **ON** = CronJob is **enabled** (`suspend=false`)
- **OFF** = CronJob is **suspended** (`suspend=true`)

**Attributes**:
- `namespace`: The namespace containing the CronJob
- `schedule`: The cron schedule (e.g., "0 2 * * *")
- `suspend` / `suspended`: Whether the CronJob is suspended
- `active_jobs_count`: Number of currently active jobs
- `last_schedule_time`: Last time the CronJob was scheduled
- `next_schedule_time`: Next scheduled execution time
- `last_suspend_time`: Timestamp when the CronJob was last suspended
- `last_resume_time`: Timestamp when the CronJob was last resumed
- `workload_type`: "CronJob"

## Services

### 1. `kubernetes.suspend_cronjob`

Suspends one or more CronJobs by setting `suspend=true`.

**Parameters**:
- `cronjob_name` (optional): Single CronJob name
- `cronjob_names` (optional): List of CronJob names
- `namespace` (optional): Target namespace (defaults to configured namespace)

**Examples**:

```yaml
# Suspend a single CronJob
service: kubernetes.suspend_cronjob
data:
  cronjob_name: backup-job
  namespace: default

# Suspend multiple CronJobs
service: kubernetes.suspend_cronjob
data:
  cronjob_names:
    - backup-job
    - cleanup-job
  namespace: production
```

### 2. `kubernetes.resume_cronjob`

Resumes one or more CronJobs by setting `suspend=false`.

**Parameters**:
- `cronjob_name` (optional): Single CronJob name
- `cronjob_names` (optional): List of CronJob names
- `namespace` (optional): Target namespace (defaults to configured namespace)

**Examples**:

```yaml
# Resume a single CronJob
service: kubernetes.resume_cronjob
data:
  cronjob_name: backup-job
  namespace: default

# Resume multiple CronJobs
service: kubernetes.resume_cronjob
data:
  cronjob_names:
    - backup-job
    - cleanup-job
  namespace: production
```

### 3. `kubernetes.create_cronjob_job`

Creates a job from one or more CronJobs (manual trigger).

**Parameters**:
- `cronjob_name` (optional): Single CronJob name
- `cronjob_names` (optional): List of CronJob names
- `namespace` (optional): Target namespace (defaults to configured namespace)

**Examples**:

```yaml
# Create a job from a single CronJob
service: kubernetes.create_cronjob_job
data:
  cronjob_name: backup-job
  namespace: default

# Create jobs from multiple CronJobs
service: kubernetes.create_cronjob_job
data:
  cronjob_names:
    - backup-job
    - cleanup-job
  namespace: production
```

### 4. `kubernetes.trigger_cronjob` (Legacy)

This service is maintained for backward compatibility and functions identically to `kubernetes.create_cronjob_job`.

## Configuration

CronJob monitoring is automatically enabled when you configure the Kubernetes integration. No additional configuration is required.

### Namespace Support

- **Single Namespace**: When configured for a specific namespace, only CronJobs in that namespace are monitored
- **All Namespaces**: When "Monitor All Namespaces" is enabled, CronJobs across all namespaces are monitored

### Permissions

CronJob functionality requires specific Kubernetes RBAC permissions:

**Required Permissions**:
- `batch/cronjobs`: `get`, `list`, `watch`, `patch`
- `batch/jobs`: `get`, `list`, `watch`, `create`
- `batch/cronjobs/status`: `get`, `patch`, `update`

**Example RBAC Rule**:
```yaml
- apiGroups: ["batch"]
  resources: ["cronjobs", "jobs"]
  verbs: ["get", "list", "watch", "patch", "create"]
- apiGroups: ["batch"]
  resources: ["cronjobs/status"]
  verbs: ["get", "patch", "update"]
```

For complete RBAC setup instructions, see the [RBAC Reference Guide](RBAC.md).

## Use Cases

### 1. Scheduled Maintenance

Use switches to suspend CronJobs during maintenance windows:

```yaml
# Suspend all backup jobs during maintenance
service: kubernetes.suspend_cronjob
data:
  cronjob_names:
    - daily-backup
    - hourly-backup
    - weekly-backup
```

### 2. Manual Job Execution

Trigger jobs manually when needed:

```yaml
# Manually trigger a backup job
service: kubernetes.create_cronjob_job
data:
  cronjob_name: backup-job
```

### 3. Conditional Job Execution

Use automations to conditionally enable/disable CronJobs:

```yaml
automation:
  - alias: "Suspend CronJobs on High Load"
    trigger:
      platform: numeric_state
      entity_id: sensor.cpu_usage
      above: 80
    action:
      service: kubernetes.suspend_cronjob
      data:
        cronjob_names:
          - non-critical-job
          - maintenance-job

  - alias: "Resume CronJobs on Normal Load"
    trigger:
      platform: numeric_state
      entity_id: sensor.cpu_usage
      below: 60
    action:
      service: kubernetes.resume_cronjob
      data:
        cronjob_names:
          - non-critical-job
          - maintenance-job
```

### 4. UI Integration

Use switches in your Home Assistant dashboard for easy control:

```yaml
# Dashboard configuration example
views:
  - title: "Kubernetes CronJobs"
    path: cronjobs
    cards:
      - type: entities
        title: "CronJob Controls"
        entities:
          - entity: switch.backup_job
            name: "Daily Backup"
          - entity: switch.cleanup_job
            name: "Cleanup Job"
          - entity: switch.maintenance_job
            name: "Maintenance Job"
```

### 5. Automated Backup Triggers

Create automations to trigger backup CronJobs based on events:

```yaml
automation:
  - alias: "Trigger Backup on Database Change"
    trigger:
      platform: state
      entity_id: sensor.database_status
      to: "modified"
    action:
      service: kubernetes.create_cronjob_job
      data:
        cronjob_name: database-backup
        namespace: production
```

### 6. Monitoring CronJob Health

Monitor CronJob execution status:

```yaml
automation:
  - alias: "Alert on CronJob Failure"
    trigger:
      platform: state
      entity_id: switch.backup_job
      to: "off"
    condition:
      condition: template
      value_template: "{{ states('sensor.backup_job_active_jobs') == '0' }}"
    action:
      service: notify.mobile_app
      data:
        message: "Backup CronJob has no active jobs - check for failures"
```

## Error Handling

All service calls include comprehensive error handling:

- **Namespace Permissions**: Services respect the `monitor_all_namespaces` configuration
- **API Errors**: Detailed error messages for API failures
- **Validation**: Input validation for CronJob names and namespaces
- **Logging**: Comprehensive logging for debugging

## Best Practices

1. **Use Switches for Regular Control**: Use switches for day-to-day CronJob management
2. **Use Services for Automation**: Use service calls in automations and scripts
3. **Monitor State Changes**: Watch the `last_suspend_time` and `last_resume_time` attributes
4. **Namespace Awareness**: Always specify the namespace when working with multiple namespaces
5. **Error Handling**: Check service call results in automations

## Migration from Previous Version

If you were using the previous CronJob switch behavior (where switches triggered jobs):

1. **Switch Behavior Changed**: Switches now control suspension instead of triggering jobs
2. **Use `kubernetes.create_cronjob_job`**: For manual job triggering, use the new service
3. **Update Automations**: Review and update any automations that used the old switch behavior
4. **New Attributes**: Take advantage of the new suspension tracking attributes

## Troubleshooting

### Common Issues

1. **Switch Not Responding**: Check if the CronJob exists and the integration has proper permissions
2. **Service Call Fails**: Verify the CronJob name and namespace are correct
3. **State Not Updating**: Check the coordinator update interval and cluster connectivity

### CronJob Not Appearing

1. **Check Permissions**: Ensure the service account has `get` and `list` permissions for `cronjobs`
2. **Verify Namespace**: Check if the CronJob is in the monitored namespace
3. **Check Integration Logs**: Look for errors in the Home Assistant logs

### Trigger Fails

1. **Check CronJob Exists**: Verify the CronJob name and namespace are correct
2. **Verify Permissions**: Ensure the service account has `create` permission for `jobs`
3. **Check CronJob Status**: Ensure the CronJob is not suspended
4. **Review Logs**: Check both Home Assistant and Kubernetes logs for errors

### No Active Jobs

1. **Check Schedule**: Verify the CronJob has a valid schedule
2. **Check Suspension**: Ensure the CronJob is not suspended
3. **Verify Concurrency Policy**: Check if the CronJob's concurrency policy is preventing new jobs

### Debug Information

Enable debug logging for the integration:

```yaml
logger:
  custom_components.kubernetes: debug
```

This will provide detailed information about CronJob operations and state changes.

## API Reference

### CronJob Data Structure

The integration provides CronJob data in the following format:

```python
{
    "name": "backup-job",
    "namespace": "default",
    "schedule": "0 2 * * *",
    "suspend": False,
    "last_schedule_time": "2023-01-01T02:00:00Z",
    "next_schedule_time": "2023-01-02T02:00:00Z",
    "active_jobs_count": 1,
    "successful_jobs_history_limit": 3,
    "failed_jobs_history_limit": 1,
    "concurrency_policy": "Allow",
    "uid": "cronjob-uid-123",
    "creation_timestamp": "2023-01-01T00:00:00Z"
}
```

### Service Response

When suspending/resuming a CronJob, the service returns:

```python
{
    "success": True,
    "cronjob_name": "backup-job",
    "namespace": "default",
    "action": "suspended"  # or "resumed"
}
```

When creating a job from a CronJob, the service returns:

```python
{
    "success": True,
    "job_name": "backup-job-manual-1234567890",
    "namespace": "default",
    "cronjob_name": "backup-job",
    "job_uid": "job-uid-123"
}
```

Or on failure:

```python
{
    "success": False,
    "error": "CronJob not found",
    "cronjob_name": "backup-job",
    "namespace": "default"
}
```
