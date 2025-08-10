# Development Guide

This document provides detailed instructions for developing and contributing to the Home Assistant Kubernetes integration.

## Prerequisites

- Python 3.12 or higher
- Home Assistant 2025.7 or higher
- A Kubernetes cluster for testing (minikube, kind, or cloud-based)
- Git

## Development Environment Setup

### 1. Clone the Repository

```bash
git clone https://github.com/tibuntu/homeassistant-kubernetes.git
cd homeassistant-kubernetes
```

### 2. Development Container (Recommended)

The easiest way to get started is using the provided devcontainer which provides a complete Home Assistant development environment.

#### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) or [Podman](https://podman.io/getting-started/installation)
- [Visual Studio Code](https://code.visualstudio.com/)
- [Dev Containers extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers)

#### Quick Start

1. **Open the project in VS Code**:
   ```bash
   code .
   ```

2. **Start the devcontainer**:
   - Press `F1` and select "Dev Containers: Reopen in Container"
   - Or click the green "Reopen in Container" button when prompted

3. **Wait for setup to complete** (first run takes a few minutes)
   - Home Assistant will start automatically after setup

4. **Access Home Assistant** at [http://localhost:8123](http://localhost:8123)
   - Wait about a minute for Home Assistant to fully start up

#### What's Included

The devcontainer automatically provides:
- ✅ Complete Home Assistant installation
- ✅ Your integration automatically mounted and available
- ✅ All development dependencies (black, isort, flake8, pytest)
- ✅ Debug logging pre-configured
- ✅ VS Code extensions for Python development
- ✅ Quick test scripts and development helpers

#### Development Workflow

1. **Edit your integration code** directly in VS Code
2. **Restart Home Assistant** to apply changes:
   - Use the restart script: `/config/restart_ha.sh`
   - Or in HA: Settings → System → Restart
3. **Check logs**:
   - Settings → System → Logs in HA UI
   - Or view log file: `tail -f /config/logs/home-assistant.log`

#### Testing Your Integration

Configure the integration by editing `.devcontainer/configuration.yaml`:

```yaml
kubernetes:
  host: "https://your-cluster-endpoint"
  token: "your-service-account-token"
  verify_ssl: false  # for development clusters
```

Or use the Home Assistant UI: Settings → Integrations → Add Integration

#### Debugging

**Enable Python debugging**:
1. Uncomment in `.devcontainer/configuration.yaml`:
   ```yaml
   debugpy:
     start: true
     wait: false
     port: 5678
   ```
2. Restart Home Assistant
3. In VS Code: Run and Debug → "Python: Remote Attach" → localhost:5678

**Code quality tools** (run automatically on save):
- `black custom_components/` - code formatting
- `isort custom_components/` - import sorting
- `flake8 custom_components/` - linting
- `pytest tests/` - run tests

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

#### General Issues

1. **Connection refused**: Check if the Kubernetes API server is accessible
2. **Authentication failed**: Verify the API token is correct
3. **SSL certificate errors**: Check CA certificate configuration
4. **Permission denied**: Ensure the ServiceAccount has proper RBAC permissions

#### Devcontainer Issues

1. **Integration not loading**:
   - Check `/config/custom_components/kubernetes/` exists in the container
   - Verify `manifest.json` is valid
   - Check Home Assistant logs: `ha logs --filter kubernetes`

2. **Permission issues**:
   - Ensure Docker has permission to mount volumes
   - On Linux, you may need to adjust file ownership

3. **Port conflicts**:
   - If port 8123 is in use, update `forwardPorts` in `.devcontainer/devcontainer.json`

4. **Container won't start**:
   - Try rebuilding: F1 → "Dev Containers: Rebuild Container"
   - Check Docker is running and has sufficient resources

**Useful devcontainer commands**:
```bash
# Start Home Assistant
/config/start_ha.sh &

# Restart Home Assistant
/config/restart_ha.sh

# Check setup
/config/check_setup.sh

# Test integration
python /config/test_integration.py

# View logs
tail -f /config/logs/home-assistant.log

# Check running processes
ps aux | grep hass
```

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
