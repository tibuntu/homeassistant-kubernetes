# Examples and Automations

This document provides practical examples of using the Kubernetes integration in Home Assistant automations and dashboards.

## Automation Examples

### Time-Based Scaling

#### Stop Multiple Deployments at Night

```yaml
automation:
  - alias: "Stop multiple deployments at night"
    trigger:
      platform: time
      at: "22:00:00"
    action:
      - service: kubernetes.stop_deployment
        data:
          deployment_names:
            - "development-api"
            - "staging-api"
            - "monitoring"
          namespace: "production"
```

#### Start Multiple Deployments in the Morning

```yaml
automation:
  - alias: "Start multiple deployments in the morning"
    trigger:
      platform: time
      at: "07:00:00"
    action:
      - service: kubernetes.start_deployment
        data:
          deployment_names:
            - "web-app"
            - "api-server"
            - "cache-service"
          replicas: 3
          namespace: "production"
```

#### Scale Down During Off-Hours

```yaml
automation:
  - alias: "Scale down for off-hours"
    trigger:
      platform: time
      at: "18:00:00"
    condition:
      condition: time
      weekday:
        - mon
        - tue
        - wed
        - thu
        - fri
    action:
      - service: kubernetes.scale_deployment
        data:
          deployment_names:
            - "web-frontend"
            - "api-backend"
          replicas: 1
          namespace: "production"
```

### Resource-Based Automations

#### Scale Up on High Load

```yaml
automation:
  - alias: "Scale up on high CPU usage"
    trigger:
      platform: numeric_state
      entity_id: sensor.server_cpu_usage
      above: 80
      for:
        minutes: 5
    action:
      - service: kubernetes.scale_deployment
        data:
          deployment_name: "web-app"
          namespace: "production"
          replicas: 5
```

#### Emergency Cluster Shutdown

```yaml
automation:
  - alias: "Emergency cluster shutdown"
    trigger:
      platform: state
      entity_id: binary_sensor.ups_power_failure
      to: "on"
    action:
      - service: kubernetes.stop_deployment
        data:
          deployment_names:
            - "non-critical-app"
            - "development-services"
          namespace: "default"
      - delay: "00:02:00"
      - service: kubernetes.scale_deployment
        data:
          deployment_names:
            - "critical-app"
          replicas: 1
          namespace: "production"
```

### StatefulSet Examples

#### Scale Database StatefulSets

```yaml
automation:
  - alias: "Scale database StatefulSets for maintenance"
    trigger:
      platform: time
      at: "02:00:00"
    condition:
      condition: time
      weekday:
        - sun
    action:
      - service: kubernetes.scale_statefulset
        data:
          statefulset_names:
            - "database-primary"
            - "database-replica"
          replicas: 1
          namespace: "database"
```

#### Stop Development Databases

```yaml
automation:
  - alias: "Stop development databases over weekend"
    trigger:
      platform: time
      at: "19:00:00"
    condition:
      condition: time
      weekday:
        - fri
    action:
      - service: kubernetes.stop_statefulset
        data:
          statefulset_names:
            - "dev-postgres"
            - "dev-redis"
          namespace: "development"
```

## Dashboard Examples

### Basic Cluster Overview

```yaml
views:
  - title: "Kubernetes Cluster"
    path: kubernetes
    cards:
      - type: entities
        title: "Cluster Status"
        entities:
          - entity: sensor.kubernetes_pods_count
            name: "Running Pods"
          - entity: sensor.kubernetes_nodes_count
            name: "Cluster Nodes"
          - entity: sensor.kubernetes_deployments_count
            name: "Active Deployments"
          - entity: binary_sensor.kubernetes_cluster_health
            name: "Cluster Health"
```

### Deployment Control Dashboard

```yaml
views:
  - title: "Deployment Control"
    path: kubernetes-deployments
    cards:
      - type: entities
        title: "Production Deployments"
        entities:
          - switch.kubernetes_deployment_web_app
          - switch.kubernetes_deployment_api_server
          - switch.kubernetes_deployment_cache_service
      - type: entities
        title: "Development Services"
        entities:
          - switch.kubernetes_deployment_dev_api
          - switch.kubernetes_deployment_test_runner
```

### Resource Monitoring

```yaml
views:
  - title: "Resource Monitoring"
    path: kubernetes-resources
    cards:
      - type: gauge
        entity: sensor.kubernetes_pods_count
        min: 0
        max: 50
        name: "Pod Count"
        severity:
          green: 0
          yellow: 30
          red: 45
      - type: history-graph
        entities:
          - sensor.kubernetes_pods_count
          - sensor.kubernetes_deployments_count
        hours_to_show: 24
```

## Script Examples

### Deployment Management Scripts

#### Scale Environment

```yaml
script:
  scale_production_environment:
    alias: "Scale Production Environment"
    sequence:
      - service: kubernetes.scale_deployment
        data:
          deployment_names:
            - "web-frontend"
            - "api-backend"
            - "worker-queue"
          replicas: "{{ replicas | default(3) }}"
          namespace: "production"
```

#### Rolling Restart

```yaml
script:
  rolling_restart_deployment:
    alias: "Rolling Restart Deployment"
    sequence:
      - service: kubernetes.scale_deployment
        data:
          deployment_name: "{{ deployment_name }}"
          namespace: "{{ namespace }}"
          replicas: 0
      - delay: "00:00:30"
      - service: kubernetes.scale_deployment
        data:
          deployment_name: "{{ deployment_name }}"
          namespace: "{{ namespace }}"
          replicas: "{{ original_replicas | default(1) }}"
```

## Notification Examples

### Deployment Failure Alerts

```yaml
automation:
  - alias: "Alert on deployment failure"
    trigger:
      platform: state
      entity_id: switch.kubernetes_deployment_critical_app
      to: "off"
      for:
        minutes: 2
    action:
      - service: notify.mobile_app
        data:
          title: "Deployment Alert"
          message: "Critical app deployment is down!"
          data:
            priority: high
```

### Cluster Health Monitoring

```yaml
automation:
  - alias: "Cluster health alert"
    trigger:
      platform: state
      entity_id: binary_sensor.kubernetes_cluster_health
      to: "off"
    action:
      - service: notify.slack
        data:
          message: "🚨 Kubernetes cluster is unhealthy!"
          target: "#devops"
```

## Advanced Examples

### Conditional Scaling Based on Day

```yaml
automation:
  - alias: "Smart scaling based on day"
    trigger:
      platform: time
      at: "08:00:00"
    action:
      - choose:
          - conditions:
              - condition: time
                weekday:
                  - mon
                  - tue
                  - wed
                  - thu
                  - fri
            sequence:
              - service: kubernetes.scale_deployment
                data:
                  deployment_name: "business-app"
                  namespace: "production"
                  replicas: 5
          - conditions:
              - condition: time
                weekday:
                  - sat
                  - sun
            sequence:
              - service: kubernetes.scale_deployment
                data:
                  deployment_name: "business-app"
                  namespace: "production"
                  replicas: 2
```

### Multi-Environment Management

```yaml
script:
  promote_to_production:
    alias: "Promote to Production"
    sequence:
      - service: kubernetes.stop_deployment
        data:
          deployment_name: "{{ app_name }}"
          namespace: "staging"
      - delay: "00:01:00"
      - service: kubernetes.start_deployment
        data:
          deployment_name: "{{ app_name }}"
          namespace: "production"
          replicas: 3
```

These examples demonstrate the flexibility of the Kubernetes integration for automating cluster management tasks directly from Home Assistant.
