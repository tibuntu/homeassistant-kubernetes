/**
 * Canned WebSocket responses served by the e2e harness, keyed by message
 * type. The shapes mirror what `websocket_api.py` sends — keep them in step
 * when a command's payload changes.
 */
export const RESPONSES: Record<string, unknown> = {
  "kubernetes/cluster/overview": {
    clusters: [
      {
        entry_id: "entry_1",
        cluster_name: "test-cluster",
        healthy: true,
        server_version: "v1.37.0",
        last_update: Math.floor(Date.now() / 1000),
        counts: {
          pods: 2,
          nodes: 1,
          deployments: 1,
          statefulsets: 1,
          daemonsets: 1,
          cronjobs: 1,
          jobs: 1,
          ingresses: 1,
          services: 1,
        },
        namespaces: { default: { pods: 2, deployments: 1, statefulsets: 1 } },
        alerts: { nodes_with_pressure: [], degraded_workloads: [], failed_pods: [] },
      },
    ],
  },

  "kubernetes/nodes/list": {
    clusters: [
      {
        entry_id: "entry_1",
        cluster_name: "test-cluster",
        nodes: [
          {
            name: "node-1",
            status: "Ready",
            internal_ip: "10.0.0.1",
            external_ip: "",
            cpu_cores: 4,
            memory_capacity_gib: 16,
            memory_allocatable_gib: 15.5,
            os_image: "Ubuntu 24.04",
            kernel_version: "6.8.0",
            container_runtime: "containerd://2.0.0",
            kubelet_version: "v1.37.0",
            schedulable: true,
            creation_timestamp: "2026-01-01T00:00:00Z",
            memory_pressure: false,
            disk_pressure: false,
            pid_pressure: false,
            network_unavailable: false,
          },
        ],
      },
    ],
  },

  "kubernetes/pods/list": {
    clusters: [
      {
        entry_id: "entry_1",
        cluster_name: "test-cluster",
        pods: [
          {
            name: "web-7d9f8b-abc12",
            namespace: "default",
            phase: "Running",
            ready_containers: 1,
            total_containers: 1,
            restart_count: 0,
            node_name: "node-1",
            pod_ip: "10.1.0.5",
            creation_timestamp: "2026-01-01T00:00:00Z",
            owner_kind: "ReplicaSet",
            owner_name: "web-7d9f8b",
          },
          {
            name: "db-0",
            namespace: "default",
            phase: "Running",
            ready_containers: 1,
            total_containers: 1,
            restart_count: 2,
            node_name: "node-1",
            pod_ip: "10.1.0.6",
            creation_timestamp: "2026-01-01T00:00:00Z",
            owner_kind: "StatefulSet",
            owner_name: "db",
          },
        ],
      },
    ],
  },

  "kubernetes/workloads/list": {
    clusters: [
      {
        entry_id: "entry_1",
        cluster_name: "test-cluster",
        deployments: [
          {
            name: "web",
            namespace: "default",
            replicas: 2,
            available_replicas: 2,
            ready_replicas: 2,
          },
        ],
        statefulsets: [
          {
            name: "db",
            namespace: "default",
            replicas: 1,
            available_replicas: 1,
            ready_replicas: 1,
          },
        ],
        daemonsets: [
          {
            name: "log-agent",
            namespace: "kube-system",
            desired_number_scheduled: 1,
            number_available: 1,
          },
        ],
        cronjobs: [
          {
            name: "backup",
            namespace: "default",
            schedule: "0 * * * *",
            suspend: false,
            last_schedule_time: null,
            active_jobs_count: 0,
          },
        ],
        jobs: [
          {
            name: "migrate",
            namespace: "default",
            completions: 1,
            succeeded: 1,
            failed: 0,
            active: 0,
            start_time: null,
          },
        ],
      },
    ],
  },

  "kubernetes/ingresses/list": {
    clusters: [
      {
        entry_id: "entry_1",
        cluster_name: "test-cluster",
        ingresses: [
          {
            name: "web",
            namespace: "default",
            ingress_class: "nginx",
            rules: [{ host: "web.example.com", service_name: "web" }],
            tls_hosts: ["web.example.com"],
            urls: ["https://web.example.com"],
            creation_timestamp: "2026-01-01T00:00:00Z",
          },
        ],
      },
    ],
  },

  "kubernetes/services/list": {
    clusters: [
      {
        entry_id: "entry_1",
        cluster_name: "test-cluster",
        services: [
          {
            name: "web",
            namespace: "default",
            type: "ClusterIP",
            cluster_ip: "10.96.0.10",
            external_ips: [],
            ports: [{ port: 80, target_port: 8080, node_port: null, protocol: "TCP" }],
            urls: [],
            creation_timestamp: "2026-01-01T00:00:00Z",
          },
        ],
      },
    ],
  },

  "kubernetes/config/list": {
    entries: [
      {
        entry_id: "entry_1",
        cluster_name: "test-cluster",
        host: "k8s.example.com",
        port: 6443,
        verify_ssl: true,
        monitor_all_namespaces: true,
        namespaces: [],
        device_grouping_mode: "namespace",
        switch_update_interval: 60,
        scale_verification_timeout: 60,
        scale_cooldown: 30,
        panel_enabled: true,
        watch_enabled: true,
        healthy: true,
      },
    ],
  },
};
