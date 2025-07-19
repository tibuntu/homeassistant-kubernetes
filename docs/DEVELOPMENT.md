# Development Guide

This document provides detailed instructions for developing and contributing to the Home Assistant Kubernetes integration.

## Prerequisites

- Python 3.9 or higher
- Home Assistant 2023.8 or higher
- A Kubernetes cluster for testing (minikube, kind, or cloud-based)
- Git

## Development Environment Setup

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/homeassistant-kubernetes.git
cd homeassistant-kubernetes
```

### 2. Run the Setup Script

```bash
./scripts/setup_dev_environment.sh
```

This script will:
- Check Python version requirements
- Create a virtual environment
- Install dependencies
- Set up the development environment
- Create necessary symlinks

### 3. Manual Setup (Alternative)

If you prefer to set up manually:

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install -e ".[dev]"

# Create Home Assistant config directory
mkdir -p config/custom_components
ln -sf "$(pwd)/custom_components/kubernetes" "config/custom_components/kubernetes"
```

## Project Structure

```
homeassistant-kubernetes/
├── custom_components/
│   └── kubernetes/
│       ├── __init__.py              # Main integration file
│       ├── manifest.json            # Integration metadata
│       ├── config_flow.py           # Configuration flow
│       ├── const.py                 # Constants and configuration keys
│       ├── sensor.py                # Sensor platform
│       ├── binary_sensor.py         # Binary sensor platform
│       ├── kubernetes_client.py     # Kubernetes API client
│       └── translations/
│           └── en.json              # English translations
├── tests/
│   └── test_kubernetes_integration.py
├── scripts/
│   └── setup_dev_environment.sh
├── docs/
│   └── DEVELOPMENT.md
├── requirements.txt
├── pyproject.toml
└── README.md
```

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run tests with verbose output
pytest -v

# Run specific test file
pytest tests/test_kubernetes_integration.py

# Run tests with coverage
pytest --cov=custom_components/kubernetes
```

### Setting Up a Test Kubernetes Cluster

#### Using minikube

```bash
# Install minikube
curl -LO https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64
sudo install minikube-linux-amd64 /usr/local/bin/minikube

# Start minikube
minikube start

# Create test resources
kubectl create namespace test-namespace
kubectl run nginx --image=nginx -n test-namespace
kubectl expose pod nginx --port=80 -n test-namespace
```

#### Using kind

```bash
# Install kind
curl -Lo ./kind https://kind.sigs.k8s.io/dl/v0.20.0/kind-linux-amd64
chmod +x ./kind
sudo mv ./kind /usr/local/bin/kind

# Create cluster
kind create cluster

# Create test resources
kubectl create namespace test-namespace
kubectl run nginx --image=nginx -n test-namespace
```

### Creating Test ServiceAccount

```yaml
# serviceaccount.yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: homeassistant-test
  namespace: default
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: homeassistant-test
subjects:
- kind: ServiceAccount
  name: homeassistant-test
  namespace: default
roleRef:
  kind: ClusterRole
  name: view
  apiGroup: rbac.authorization.k8s.io
```

Apply the configuration:

```bash
kubectl apply -f serviceaccount.yaml
```

Get the token:

```bash
kubectl get secret $(kubectl get serviceaccount homeassistant-test -o jsonpath='{.secrets[0].name}') -o jsonpath='{.data.token}' | base64 --decode
```

## Code Quality

### Code Formatting

```bash
# Format code with black
black .

# Sort imports with isort
isort .

# Check code style with flake8
flake8 .
```

### Type Checking

```bash
# Run mypy type checking
mypy custom_components/kubernetes/
```

### Pre-commit Hooks

Install pre-commit hooks:

```bash
pip install pre-commit
pre-commit install
```

## Integration Testing

### Manual Testing

1. Start Home Assistant with your development configuration:

```bash
hass --config config
```

2. Open Home Assistant in your browser (usually http://localhost:8123)

3. Go to **Settings** → **Devices & Services** → **Add Integration**

4. Search for "Kubernetes" and add it

5. Configure the integration with your test cluster details

6. Verify that sensors are created and updating

### Automated Testing

Create integration tests in `tests/` directory:

```python
import pytest
from homeassistant.const import CONF_HOST, CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from custom_components.kubernetes.const import DOMAIN


async def test_load_unload_config_entry(hass: HomeAssistant) -> None:
    """Test loading and unloading the config entry."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_NAME: "Test Kubernetes",
            CONF_HOST: "test-cluster.example.com",
            # ... other config
        },
    )
    config_entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    assert await hass.config_entries.async_unload(config_entry.entry_id)
    await hass.async_block_till_done()
```

## Debugging

### Enable Debug Logging

Add to your `configuration.yaml`:

```yaml
logger:
  default: info
  logs:
    custom_components.kubernetes: debug
```

### Common Issues

1. **Connection refused**: Check if the Kubernetes API server is accessible
2. **Authentication failed**: Verify the API token is correct
3. **SSL certificate errors**: Check CA certificate configuration
4. **Permission denied**: Ensure the ServiceAccount has proper RBAC permissions

## Contributing

### Pull Request Process

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass: `pytest`
6. Format your code: `black . && isort .`
7. Commit your changes: `git commit -m 'Add amazing feature'`
8. Push to the branch: `git push origin feature/amazing-feature`
9. Open a Pull Request

### Code Review Checklist

- [ ] Code follows Home Assistant integration patterns
- [ ] All tests pass
- [ ] Code is properly formatted
- [ ] Type hints are included
- [ ] Documentation is updated
- [ ] No sensitive information is exposed

## Resources

- [Home Assistant Developer Documentation](https://developers.home-assistant.io/)
- [Kubernetes Python Client](https://github.com/kubernetes-client/python)
- [Home Assistant Integration Guidelines](https://developers.home-assistant.io/docs/creating_integration_manifest/)
- [Home Assistant Architecture](https://developers.home-assistant.io/docs/architecture_index/)
