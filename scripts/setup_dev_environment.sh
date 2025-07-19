#!/bin/bash

# Development setup script for Home Assistant Kubernetes Integration

set -e

echo "Setting up development environment for Home Assistant Kubernetes Integration..."

# Check if Python 3.9+ is available
python_version=$(python3 --version 2>&1 | awk '{print $2}' | cut -d. -f1,2)
required_version="3.9"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "Error: Python 3.9 or higher is required. Found: $python_version"
    exit 1
fi

echo "Python version check passed: $python_version"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Install development dependencies
echo "Installing development dependencies..."
pip install -e ".[dev]"

# Create symlink for Home Assistant development
echo "Setting up Home Assistant development environment..."
if [ ! -d "config" ]; then
    mkdir -p config
fi

if [ ! -d "config/custom_components" ]; then
    mkdir -p config/custom_components
fi

# Create symlink to custom_components
if [ ! -L "config/custom_components/kubernetes" ]; then
    ln -sf "$(pwd)/custom_components/kubernetes" "config/custom_components/kubernetes"
    echo "Created symlink: config/custom_components/kubernetes"
fi

echo ""
echo "Development environment setup complete!"
echo ""
echo "Next steps:"
echo "1. Start Home Assistant with: hass --config config"
echo "2. Go to Settings > Devices & Services > Add Integration"
echo "3. Search for 'Kubernetes' and configure it"
echo "4. Run tests with: pytest"
echo "5. Format code with: black . && isort ."
echo ""
echo "Happy coding!"
