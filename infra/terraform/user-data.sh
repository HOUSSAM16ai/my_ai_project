#!/bin/bash
# User data script for GPU nodes
# Installs NVIDIA drivers and configures EKS

set -ex

# Bootstrap EKS node
/etc/eks/bootstrap.sh ${cluster_name}

# Install NVIDIA driver
amazon-linux-extras install -y nvidia-driver-latest-dkms
modprobe nvidia

# Install NVIDIA container toolkit
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | tee /etc/apt/sources.list.d/nvidia-docker.list

apt-get update && apt-get install -y nvidia-container-toolkit
systemctl restart docker

# Configure containerd for NVIDIA
cat > /etc/containerd/config.toml <<EOF
version = 2
[plugins."io.containerd.grpc.v1.cri".containerd]
  default_runtime_name = "nvidia"
  [plugins."io.containerd.grpc.v1.cri".containerd.runtimes.nvidia]
    privileged_without_host_devices = false
    runtime_engine = ""
    runtime_root = ""
    runtime_type = "io.containerd.runc.v2"
    [plugins."io.containerd.grpc.v1.cri".containerd.runtimes.nvidia.options]
      BinaryName = "/usr/bin/nvidia-container-runtime"
EOF

systemctl restart containerd

# Verify NVIDIA setup
nvidia-smi
