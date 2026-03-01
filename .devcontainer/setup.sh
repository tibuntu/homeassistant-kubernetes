#!/bin/bash

# Home Assistant Kubernetes Integration Devcontainer Setup Script

set -e

echo "🚀 Setting up Home Assistant Kubernetes Integration development environment..."

# Update system packages
echo "📦 Updating system packages..."
sudo apt-get update
sudo apt-get install -y \
    build-essential \
    pkg-config \
    libffi-dev \
    libssl-dev \
    libjpeg-dev \
    zlib1g-dev \
    autoconf \
    automake \
    libtool \
    ffmpeg \
    libavformat-dev \
    libavcodec-dev \
    libavdevice-dev \
    libavutil-dev \
    libswscale-dev \
    libswresample-dev \
    libavfilter-dev \
    libtiff5-dev \
    libjpeg62-turbo-dev \
    libopenjp2-7-dev \
    libfreetype6-dev \
    liblcms2-dev \
    libwebp-dev \
    tcl8.6-dev \
    tk8.6-dev \
    python3-tk \
    libharfbuzz-dev \
    libfribidi-dev \
    libxcb1-dev \
    libpcap-dev \
    libpcap0.8

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install --upgrade pip setuptools wheel

# Install integration dependencies first (including kubernetes package)
echo "📦 Installing integration dependencies..."
pip install -r /workspaces/homeassistant-kubernetes/requirements.txt

# Ensure kubernetes package is installed (explicit installation for reliability)
echo "🔧 Ensuring kubernetes package is available..."
pip install kubernetes==33.1.0

# Verify kubernetes package installation
echo "🔍 Verifying kubernetes package installation..."
python3 -c "import kubernetes.client; print('✅ kubernetes.client import successful')" || {
    echo "❌ kubernetes package not properly installed, trying alternative installation..."
    pip uninstall -y kubernetes
    pip install --no-cache-dir kubernetes==33.1.0
    python3 -c "import kubernetes.client; print('✅ kubernetes.client import successful after retry')"
}

# Install Home Assistant (after ensuring dependencies are available)
echo "🏠 Installing Home Assistant..."
pip install homeassistant

# Install development dependencies
echo "🛠️ Installing development dependencies..."
pip install black isort flake8 pytest pytest-homeassistant-custom-component mypy

# Install performance libraries to address warnings
echo "📈 Installing performance libraries..."
pip install zlib-ng isal

# Create Home Assistant config directory structure
echo "📁 Setting up Home Assistant config directory..."
sudo mkdir -p /config/custom_components
sudo mkdir -p /config/logs
sudo mkdir -p /config/blueprints/automation
sudo mkdir -p /config/blueprints/script

# Fix ownership of config directory
echo "🔧 Setting up permissions..."
sudo chown -R vscode:vscode /config

# Copy configuration files
echo "🔧 Setting up configuration..."
cp /workspaces/homeassistant-kubernetes/.devcontainer/configuration.yaml /config/configuration.yaml
cp /workspaces/homeassistant-kubernetes/.devcontainer/automations.yaml /config/automations.yaml
cp /workspaces/homeassistant-kubernetes/.devcontainer/scripts.yaml /config/scripts.yaml
cp /workspaces/homeassistant-kubernetes/.devcontainer/scenes.yaml /config/scenes.yaml

# Set up symbolic link for the custom component
echo "🔗 Linking custom component..."
ln -sf /workspaces/homeassistant-kubernetes/custom_components/kubernetes /config/custom_components/kubernetes

# Create startup script
cat > /config/start_ha.sh << 'EOF'
#!/bin/bash
echo "🏠 Starting Home Assistant..."
cd /config
hass --config /config --log-file /config/logs/home-assistant.log &
disown
EOF

chmod +x /config/start_ha.sh

# Create development helper scripts
cat > /config/restart_ha.sh << 'EOF'
#!/bin/bash
echo "🔄 Restarting Home Assistant..."
pkill -f "hass --config" || true
sleep 2
/config/start_ha.sh &
echo "✅ Home Assistant restarted"
EOF

chmod +x /config/restart_ha.sh

cat > /config/logs.sh << 'EOF'
#!/bin/bash
tail -f /config/logs/home-assistant.log
EOF

chmod +x /config/logs.sh

cat > /config/test_integration.py << 'EOF'
#!/usr/bin/env python3
"""Quick test script for the Kubernetes integration."""

import asyncio
import logging
import sys
import os

# Add the custom components to the path
sys.path.insert(0, '/config/custom_components')
sys.path.insert(0, '/workspaces/homeassistant-kubernetes/custom_components')

from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

async def test_integration():
    """Test the Kubernetes integration setup."""
    logger.info("Testing Kubernetes integration...")

    hass = HomeAssistant()
    await hass.async_start()

    config = {
        "kubernetes": {}
    }

    try:
        result = await async_setup_component(hass, "kubernetes", config)
        logger.info(f"Integration setup result: {result}")

        if result:
            logger.info("✅ Kubernetes integration loaded successfully!")
        else:
            logger.error("❌ Failed to load Kubernetes integration")

    except Exception as e:
        logger.error(f"❌ Error testing integration: {e}")
    finally:
        await hass.async_stop()

if __name__ == "__main__":
    asyncio.run(test_integration())
EOF

chmod +x /config/test_integration.py

# Create a simple check script
cat > /config/check_setup.sh << 'EOF'
#!/bin/bash
echo "🔍 Checking development environment..."

echo "📁 Custom components directory:"
ls -la /config/custom_components/

echo "🔗 Kubernetes integration link:"
ls -la /config/custom_components/kubernetes

echo "📄 Configuration file:"
head -10 /config/configuration.yaml

echo "🐍 Python packages:"
pip list | grep -E "(homeassistant|kubernetes)"

echo "🧪 Testing kubernetes package import:"
python3 -c "import kubernetes.client; print('✅ kubernetes.client import works')" || echo "❌ kubernetes.client import failed"

echo "🧪 Testing Home Assistant python environment:"
hass --version 2>/dev/null || echo "❌ Home Assistant not accessible via command line"

echo "🧪 Testing integration imports:"
python3 -c "
import sys
# Add custom components to end of path, not beginning
sys.path.append('/config/custom_components')
sys.path.append('/workspaces/homeassistant-kubernetes/custom_components')
try:
    # Test kubernetes package first
    import kubernetes.client
    print('✅ kubernetes.client import works')

    # Test our integration with proper import
    from custom_components.kubernetes import config_flow
    print('✅ config_flow import works')
except Exception as e:
    print(f'❌ Integration import failed: {e}')
"

echo "✅ Environment check complete!"
EOF

chmod +x /config/check_setup.sh

echo ""
echo "🔍 Final verification of environment..."
echo "Testing kubernetes package in Home Assistant python environment:"
/usr/local/bin/python -c "import kubernetes.client; print('✅ kubernetes.client available in HA python')" || {
    echo "❌ kubernetes not available in HA python, installing globally..."
    /usr/local/bin/python -m pip install kubernetes==33.1.0
    /usr/local/bin/python -c "import kubernetes.client; print('✅ kubernetes.client now available in HA python')"
}

# Test that the kubernetes package can be imported WITHOUT our custom component in the path
echo "Testing kubernetes package import (without custom component path):"
/usr/local/bin/python -c "
try:
    import kubernetes.client
    print('✅ kubernetes.client imports successfully without path conflicts')
except Exception as e:
    print(f'❌ kubernetes.client import failed: {e}')
"

# Test that our integration can be imported with proper path ordering
echo "Testing integration imports with proper path ordering:"
/usr/local/bin/python -c "
import sys
import os

# Ensure system packages are found first, then custom components
sys.path = [p for p in sys.path if 'custom_components' not in p]  # Remove custom component paths
sys.path.extend(['/config/custom_components', '/workspaces/homeassistant-kubernetes/custom_components'])

try:
    # First test kubernetes package
    import kubernetes.client
    print('✅ kubernetes.client imports successfully with reordered path')

    # Then test our integration
    from custom_components.kubernetes import config_flow
    print('✅ config_flow imports successfully with proper path')
except Exception as e:
    print(f'❌ Import test failed: {e}')
"

echo ""
echo "✅ Development environment setup complete!"
echo ""
echo "Home Assistant will start automatically on every container start."
echo ""
echo "📖 Home Assistant: http://localhost:8123"
echo "📁 Integration linked to /config/custom_components/kubernetes"
echo ""
echo "🔄 To restart Home Assistant: /config/restart_ha.sh"
echo "🧪 To test integration: python /config/test_integration.py"
echo "🔍 To check setup: /config/check_setup.sh"
echo "📊 To view logs: tail -f /config/logs/home-assistant.log"
