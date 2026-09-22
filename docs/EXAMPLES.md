# Examples and Automations

This document provides practical examples of using the Kubernetes integration in Home Assistant automations and dashboards. Entity IDs below use `production` as the example cluster name — substitute the cluster name you chose when adding the integration (see [Entity Naming](ENTITIES.md#entity-naming)).

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
      - service: kubernetes.stop_workload
        data:
          workload_names:
            - switch.development_api
            - switch.staging_api
            - switch.monitoring
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
      - service: kubernetes.start_workload
        data:
          workload_names:
            - switch.web_app
            - switch.api_server
            - switch.cache_service
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
      - service: kubernetes.scale_workload
        data:
          workload_names:
            - switch.web_frontend
            - switch.api_backend
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
      - service: kubernetes.scale_workload
        data:
          workload_name: switch.web_app
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
      - service: kubernetes.stop_workload
        data:
          workload_names:
            - switch.non_critical_app
            - switch.development_services
          namespace: "default"
      - delay: "00:02:00"
      - service: kubernetes.scale_workload
        data:
          workload_names:
            - switch.critical_app
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
      - service: kubernetes.scale_workload
        data:
          workload_names:
            - switch.database_primary
            - switch.database_replica
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
      - service: kubernetes.stop_workload
        data:
          workload_names:
            - switch.dev_postgres
            - switch.dev_redis
          namespace: "development"
```

### Rollout Restart Examples

#### Restart Deployment via Button

```yaml
automation:
  - alias: "Restart web app on button press"
    trigger:
      platform: state
      entity_id: input_button.restart_web_app
    action:
      - service: kubernetes.restart_workload
        data:
          workload_name: "web-app"
          namespace: "production"
```

#### Scheduled Rolling Restart

```yaml
automation:
  - alias: "Weekly rolling restart of all workloads"
    trigger:
      platform: time
      at: "04:00:00"
    condition:
      condition: time
      weekday:
        - sun
    action:
      - service: kubernetes.restart_workload
        data:
          workload_names:
            - switch.production_web_app
            - switch.production_api_server
          namespace: "production"
```

### Node Monitoring Automations

#### Alert on Node Not Ready

```yaml
automation:
  - alias: "Alert on node not ready"
    trigger:
      - platform: state
        entity_id:
          - sensor.production_master_1
          - sensor.production_worker_1
          - sensor.production_worker_2
        to: "NotReady"
        for:
          minutes: 2
    action:
      - service: notify.mobile_app_your_phone
        data:
          title: "Kubernetes Node Alert"
          message: >
            Node {{ trigger.entity_id.split('.')[-1].replace('production_', '').replace('_', '-') }}
            is not ready. Status: {{ trigger.to_state.state }}
          data:
            priority: high
```

#### Monitor Node Resource Usage

```yaml
automation:
  - alias: "High memory usage alert"
    trigger:
      - platform: template
        value_template: >
          {# Node sensors are identified by the OS_image attribute, since their
             entity_id no longer has a distinguishing prefix (see Entity Naming). #}
          {% set nodes = states.sensor | selectattr('attributes.OS_image', 'defined') | list %}
          {% for node in nodes %}
            {# memory_capacity_(GiB) / memory_allocatable_(GiB) are formatted
               strings like "16 GiB" — strip the unit before casting to float. #}
            {% set capacity = state_attr(node.entity_id, 'memory_capacity_(GiB)') %}
            {% set allocatable = state_attr(node.entity_id, 'memory_allocatable_(GiB)') %}
            {% if capacity and allocatable %}
              {% set memory_total = capacity.split(' ')[0] | float %}
              {% set memory_used = memory_total - (allocatable.split(' ')[0] | float) %}
              {% if memory_total > 0 and memory_used / memory_total > 0.9 %}
                true
              {% endif %}
            {% endif %}
          {% endfor %}
    action:
      - service: notify.persistent_notification
        data:
          title: "High Memory Usage"
          message: >
            One or more nodes are running low on memory.
            Check the node monitoring dashboard for details.
```

#### Log Node Status Changes

```yaml
automation:
  - alias: "Log node status changes"
    trigger:
      - platform: state
        entity_id:
          - sensor.production_master_1
          - sensor.production_worker_1
          - sensor.production_worker_2
    condition:
      - condition: template
        value_template: "{{ trigger.from_state.state != trigger.to_state.state }}"
    action:
      - service: logbook.log
        data:
          name: "Kubernetes Node Status"
          message: >
            Node {{ trigger.entity_id.split('.')[-1].replace('production_', '').replace('_', '-') }}
            changed from {{ trigger.from_state.state }} to {{ trigger.to_state.state }}
          entity_id: "{{ trigger.entity_id }}"
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
          - entity: sensor.production_pods_count
            name: "Running Pods"
          - entity: sensor.production_nodes_count
            name: "Cluster Nodes"
          - entity: sensor.production_deployments_count
            name: "Active Deployments"
          - entity: sensor.production_statefulsets_count
            name: "StatefulSets"
          - entity: sensor.production_cronjobs_count
            name: "CronJobs"
          - entity: binary_sensor.production_cluster_health
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
          - switch.production_default_web_app_deployment
          - switch.production_default_api_server_deployment
          - switch.production_default_cache_service_deployment
      - type: entities
        title: "Development Services"
        entities:
          - switch.production_default_dev_api_deployment
          - switch.production_default_test_runner_deployment
```

### Resource Monitoring

```yaml
views:
  - title: "Resource Monitoring"
    path: kubernetes-resources
    cards:
      - type: gauge
        entity: sensor.production_pods_count
        min: 0
        max: 50
        name: "Pod Count"
        severity:
          green: 0
          yellow: 30
          red: 45
      - type: history-graph
        entities:
          - sensor.production_pods_count
          - sensor.production_deployments_count
        hours_to_show: 24

### Node Monitoring Dashboard

```yaml
views:
  - title: "Node Status"
    path: kubernetes-nodes
    cards:
      - type: entities
        title: "Node Overview"
        entities:
          - entity: sensor.production_master_1
            name: "Master Node"
          - entity: sensor.production_worker_1
            name: "Worker Node 1"
          - entity: sensor.production_worker_2
            name: "Worker Node 2"
        show_header_toggle: false
      - type: custom:auto-entities
        card:
          type: entities
          title: "All Cluster Nodes"
        filter:
          include:
            # Filtering by the OS_image attribute (unique to node sensors) instead
            # of an entity_id wildcard, since node sensor IDs no longer have a
            # distinguishing prefix (see Entity Naming) and a "sensor.production_*"
            # wildcard would also match the count sensors.
            - attributes:
                OS_image: ".*"
        sort:
          method: name
      - type: markdown
        content: >
          ## Node Resources

          **{{ states('sensor.production_worker_1') }}** Worker 1:
          - Memory: {{ state_attr('sensor.production_worker_1', 'memory_allocatable_(GiB)') }} / {{ state_attr('sensor.production_worker_1', 'memory_capacity_(GiB)') }}
          - CPU: {{ state_attr('sensor.production_worker_1', 'CPU') }}
          - Internal IP: {{ state_attr('sensor.production_worker_1', 'internal_IP') }}
          - OS: {{ state_attr('sensor.production_worker_1', 'OS_image') }}
```

## Script Examples

### Deployment Management Scripts

#### Scale Environment

```yaml
script:
  scale_production_environment:
    alias: "Scale Production Environment"
    sequence:
      - service: kubernetes.scale_workload
        data:
          workload_names:
            - switch.web_frontend
            - switch.api_backend
            - switch.worker_queue
          replicas: "{{ replicas | default(3) }}"
          namespace: "production"
```

#### Rolling Restart

```yaml
script:
  rolling_restart_deployment:
    alias: "Rolling Restart Deployment"
    sequence:
      - service: kubernetes.scale_workload
        data:
          workload_name: "{{ workload_name }}"
          namespace: "{{ namespace }}"
          replicas: 0
      - delay: "00:00:30"
      - service: kubernetes.scale_workload
        data:
          workload_name: "{{ workload_name }}"
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
      entity_id: switch.production_default_critical_app_deployment
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
      entity_id: binary_sensor.production_cluster_health
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
              - service: kubernetes.scale_workload
                data:
                  workload_name: switch.business_app
                  namespace: "production"
                  replicas: 5
          - conditions:
              - condition: time
                weekday:
                  - sat
                  - sun
            sequence:
              - service: kubernetes.scale_workload
                data:
                  workload_name: switch.business_app
                  namespace: "production"
                  replicas: 2
```

### Multi-Environment Management

```yaml
script:
  promote_to_production:
    alias: "Promote to Production"
    sequence:
      - service: kubernetes.stop_workload
        data:
          workload_name: "{{ workload_name }}"
          namespace: "staging"
      - delay: "00:01:00"
      - service: kubernetes.start_workload
        data:
          workload_name: "{{ workload_name }}"
          namespace: "production"
          replicas: 3
```

These examples demonstrate the flexibility of the Kubernetes integration for automating cluster management tasks directly from Home Assistant.
