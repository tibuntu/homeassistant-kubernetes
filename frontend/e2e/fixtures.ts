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
          deployments: 2,
          statefulsets: 1,
          daemonsets: 1,
          cronjobs: 1,
          jobs: 2,
          ingresses: 1,
          services: 1,
        },
        namespaces: { default: { pods: 2, deployments: 2, statefulsets: 1 } },
        alerts: {
          nodes_with_pressure: [],
          degraded_workloads: [
            {
              name: "api",
              type: "Deployment",
              namespace: "default",
              ready: 2,
              desired: 2,
              reason: "ProgressDeadlineExceeded",
            },
          ],
          failed_pods: [
            {
              name: "crash-5c8d7-xyz99",
              namespace: "default",
              phase: "Running",
              reason: "CrashLoopBackOff",
            },
          ],
          restarting_pods: [
            {
              name: "worker-abc",
              namespace: "default",
              restarts: 5,
              last_terminated_reason: "OOMKilled",
              last_terminated_exit_code: 137,
              last_terminated_at: "2026-11-02T11:00:00Z",
            },
          ],
          failed_jobs: [
            {
              name: "backup-29000000",
              namespace: "default",
              cronjob: "backup",
              reason: "BackoffLimitExceeded",
              message: "Job has reached the specified backoff limit",
              failed_at: "2026-11-02T02:10:00Z",
            },
          ],
        },
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
        pod_logs_enabled: true,
        metrics_available: true,
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
            containers: ["web"],
            cpu_usage: 120,
            memory_usage: 256,
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
            containers: ["db", "metrics-exporter"],
            cpu_usage: 15,
            memory_usage: 1024,
          },
          {
            name: "crash-5c8d7-xyz99",
            namespace: "default",
            phase: "Running",
            problem: true,
            problem_reason: "CrashLoopBackOff",
            ready_containers: 0,
            total_containers: 1,
            restart_count: 7,
            node_name: "node-1",
            pod_ip: "10.1.0.7",
            creation_timestamp: "2026-01-01T00:00:00Z",
            owner_kind: "ReplicaSet",
            owner_name: "crash-5c8d7",
            containers: ["crash"],
            cpu_usage: 50,
            memory_usage: 512,
          },
        ],
      },
    ],
  },

  "kubernetes/pods/describe": {
    pod: {
      name: "db-0",
      namespace: "default",
      phase: "Running",
      reason: null,
      message: null,
      node_name: "node-1",
      pod_ip: "10.1.0.6",
      qos_class: "Burstable",
      creation_timestamp: "2026-01-01T00:00:00Z",
      owner_kind: "StatefulSet",
      owner_name: "db",
      containers: [
        {
          name: "wait-for-disk",
          image: "busybox:1.37",
          init: true,
          ready: true,
          restart_count: 0,
          state: { state: "terminated", reason: "Completed", exit_code: 0 },
          last_state: { state: null },
        },
        {
          name: "db",
          image: "postgres:17",
          init: false,
          ready: true,
          restart_count: 0,
          state: { state: "running", started_at: "2026-01-01T00:00:10Z" },
          last_state: { state: null },
        },
        {
          name: "metrics-exporter",
          image: "exporter:2",
          init: false,
          ready: false,
          restart_count: 2,
          state: {
            state: "waiting",
            reason: "CrashLoopBackOff",
            message: "back-off 40s restarting failed container",
          },
          last_state: {
            state: "terminated",
            reason: "OOMKilled",
            exit_code: 137,
            finished_at: "2026-01-01T00:05:00Z",
          },
        },
      ],
      conditions: [
        { type: "Ready", status: "False", reason: "ContainersNotReady", message: null },
      ],
    },
    events: [
      {
        type: "Warning",
        reason: "BackOff",
        message: "Back-off restarting failed container metrics-exporter",
        count: 12,
        timestamp: "2026-01-01T00:06:00Z",
      },
      {
        type: "Normal",
        reason: "Scheduled",
        message: "Successfully assigned default/db-0 to node-1",
        count: 1,
        timestamp: "2026-01-01T00:00:01Z",
      },
    ],
    events_error: null,
  },

  "kubernetes/pods/logs": {
    logs: `starting server\nlistening on :8080\n${"x".repeat(600)}\n`,
    truncated: false,
  },

  "kubernetes/workloads/list": {
    clusters: [
      {
        entry_id: "entry_1",
        cluster_name: "test-cluster",
        metrics_available: true,
        deployments: [
          {
            name: "web",
            namespace: "default",
            replicas: 2,
            available_replicas: 2,
            ready_replicas: 2,
            hpa_managed: false,
            hpa_name: null,
            hpa_min_replicas: null,
            hpa_max_replicas: null,
            cpu_usage: 340,
            memory_usage: 512,
          },
          {
            name: "api",
            namespace: "default",
            replicas: 2,
            available_replicas: 2,
            ready_replicas: 2,
            updated_replicas: 1,
            rollout_stalled: true,
            rollout_reason: "ProgressDeadlineExceeded",
            hpa_managed: false,
            hpa_name: null,
            hpa_min_replicas: null,
            hpa_max_replicas: null,
          },
        ],
        statefulsets: [
          {
            name: "db",
            namespace: "default",
            replicas: 1,
            available_replicas: 1,
            ready_replicas: 1,
            hpa_managed: true,
            hpa_name: "db-hpa",
            hpa_min_replicas: 1,
            hpa_max_replicas: 5,
          },
        ],
        daemonsets: [
          {
            name: "log-agent",
            namespace: "kube-system",
            desired_number_scheduled: 1,
            number_available: 1,
            cpu_usage: 5,
            memory_usage: 32,
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
            state: "Complete",
            start_time: null,
          },
          {
            name: "nightly-report",
            namespace: "default",
            completions: 1,
            succeeded: 0,
            failed: 7,
            active: 0,
            state: "Failed",
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

  "kubernetes/httproutes/list": {
    clusters: [
      {
        entry_id: "entry_1",
        cluster_name: "test-cluster",
        httproutes: [
          {
            name: "web",
            namespace: "default",
            hostnames: ["web.example.com"],
            parent_refs: [{ name: "eg", namespace: "default", section_name: "https" }],
            rules: [
              {
                matches: [{ path_type: "PathPrefix", path_value: "/", method: "" }],
                backend_refs: [{ name: "web", namespace: "default", port: 8080 }],
              },
            ],
            urls: ["https://web.example.com"],
            accepted: true,
            resolved_refs: true,
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
        panel_admin_only: false,
        watch_enabled: true,
        pod_logs_enabled: true,
        healthy: true,
      },
    ],
  },
};

/** Responses of services called with `returnResponse`, keyed by service name. */
export const SERVICE_RESPONSES: Record<string, unknown> = {
  drain_node: {
    "node-1": {
      evicted: ["default/web-7d9f8b-abc12"],
      skipped: [
        { pod: "kube-system/kube-proxy-x1y2z", reason: "daemonset" },
        { pod: "default/debug", reason: "unmanaged" },
      ],
      blocked: ["default/db-0"],
    },
  },
};
