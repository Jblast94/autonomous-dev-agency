#!/bin/bash
set -e

# MicroK8s Bootstrap Script for Autonomous Agency
# Usage: ./bootstrap-microk8s.sh [role]
# role: "master" (default) or "worker"

ROLE=${1:-master}
USER_NAME=${SUDO_USER:-$USER}

echo "🚀 Bootstrapping MicroK8s for Autonomous Agency ($ROLE)..."

# 1. Install MicroK8s
if ! command -v microk8s &> /dev/null; then
    echo "Installing MicroK8s via Snap..."
    sudo snap install microk8s --classic
else
    echo "MicroK8s is already installed."
fi

# 2. Permissions
echo "Configuring permissions for user $USER_NAME..."
sudo usermod -a -G microk8s $USER_NAME
sudo chown -f -R $USER_NAME ~/.kube

# 3. Wait for start
echo "Waiting for MicroK8s to start..."
microk8s status --wait-ready

# 4. Enable Addons (Master only or as needed)
if [ "$ROLE" == "master" ]; then
    echo "Enabling essential addons..."
    microk8s enable dns
    microk8s enable storage
    microk8s enable dashboard
    microk8s enable ingress
    microk8s enable registry
    microk8s enable metrics-server

    echo "Creating alias for kubectl..."
    snap alias microk8s.kubectl kubectl

    echo "✅ Master Node Setup Complete!"
    echo "To add a worker node, run: 'microk8s add-node'"
    echo "Then copy the output command and run it on the worker machine."
else
    echo "✅ Worker Node prerequisites installed!"
    echo "Now run the join command provided by the master node."
fi

# 5. Export Kubeconfig (Optional, useful for remote management)
microk8s config > client.config
echo "Saved kubeconfig to ./client.config (keep this safe!)"
