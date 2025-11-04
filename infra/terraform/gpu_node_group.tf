# GPU Node Group Configuration for ML Workloads
# Superhuman infrastructure for AI/ML training and inference

terraform {
  required_version = ">= 1.5.0"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.23"
    }
  }
  
  backend "s3" {
    bucket         = "cogniforge-terraform-state"
    key            = "ml-platform/gpu-nodes/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "terraform-state-locks"
  }
}

provider "aws" {
  region = var.aws_region
  
  default_tags {
    tags = {
      Project     = "CogniForge"
      ManagedBy   = "Terraform"
      Environment = var.environment
      Component   = "ML-Platform"
    }
  }
}

# Data sources
data "aws_eks_cluster" "main" {
  name = var.cluster_name
}

data "aws_eks_cluster_auth" "main" {
  name = var.cluster_name
}

# GPU Node Group for ML Training
resource "aws_eks_node_group" "gpu_training" {
  cluster_name    = data.aws_eks_cluster.main.name
  node_group_name = "${var.cluster_name}-gpu-training"
  node_role_arn   = aws_iam_role.gpu_node_role.arn
  subnet_ids      = var.private_subnet_ids

  # Instance types with GPU
  instance_types = [
    "g5.xlarge",   # 1x NVIDIA A10G, 4 vCPUs, 16GB RAM
    "g5.2xlarge",  # 1x NVIDIA A10G, 8 vCPUs, 32GB RAM
  ]

  # Spot instances for cost optimization
  capacity_type = var.use_spot_instances ? "SPOT" : "ON_DEMAND"

  # Scaling configuration
  scaling_config {
    min_size     = var.gpu_training_min_size
    desired_size = var.gpu_training_desired_size
    max_size     = var.gpu_training_max_size
  }

  # Update configuration
  update_config {
    max_unavailable_percentage = 25
  }

  # Launch template
  launch_template {
    id      = aws_launch_template.gpu_training.id
    version = "$Latest"
  }

  # Labels for pod scheduling
  labels = {
    "workload"      = "ml-training"
    "accelerator"   = "nvidia"
    "node-type"     = "gpu"
    "instance-type" = "g5"
    "cost-type"     = var.use_spot_instances ? "spot" : "on-demand"
  }

  # Taints to ensure only GPU workloads run here
  taint {
    key    = "nvidia.com/gpu"
    value  = "present"
    effect = "NO_SCHEDULE"
  }

  # Tags
  tags = {
    Name        = "${var.cluster_name}-gpu-training"
    Workload    = "ML-Training"
    Accelerator = "NVIDIA-A10G"
  }

  lifecycle {
    create_before_destroy = true
    ignore_changes       = [scaling_config[0].desired_size]
  }

  depends_on = [
    aws_iam_role_policy_attachment.gpu_node_AmazonEKSWorkerNodePolicy,
    aws_iam_role_policy_attachment.gpu_node_AmazonEKS_CNI_Policy,
    aws_iam_role_policy_attachment.gpu_node_AmazonEC2ContainerRegistryReadOnly,
  ]
}

# GPU Node Group for ML Serving/Inference
resource "aws_eks_node_group" "gpu_serving" {
  cluster_name    = data.aws_eks_cluster.main.name
  node_group_name = "${var.cluster_name}-gpu-serving"
  node_role_arn   = aws_iam_role.gpu_node_role.arn
  subnet_ids      = var.private_subnet_ids

  # Smaller GPU instances for serving
  instance_types = [
    "g5.xlarge",  # 1x NVIDIA A10G
  ]

  capacity_type = "ON_DEMAND"  # Always on-demand for serving

  scaling_config {
    min_size     = var.gpu_serving_min_size
    desired_size = var.gpu_serving_desired_size
    max_size     = var.gpu_serving_max_size
  }

  update_config {
    max_unavailable_percentage = 10  # More conservative for serving
  }

  launch_template {
    id      = aws_launch_template.gpu_serving.id
    version = "$Latest"
  }

  labels = {
    "workload"      = "ml-serving"
    "accelerator"   = "nvidia"
    "node-type"     = "gpu"
    "instance-type" = "g5"
    "cost-type"     = "on-demand"
  }

  taint {
    key    = "nvidia.com/gpu"
    value  = "present"
    effect = "NO_SCHEDULE"
  }

  tags = {
    Name        = "${var.cluster_name}-gpu-serving"
    Workload    = "ML-Serving"
    Accelerator = "NVIDIA-A10G"
  }

  lifecycle {
    create_before_destroy = true
    ignore_changes       = [scaling_config[0].desired_size]
  }

  depends_on = [
    aws_iam_role_policy_attachment.gpu_node_AmazonEKSWorkerNodePolicy,
    aws_iam_role_policy_attachment.gpu_node_AmazonEKS_CNI_Policy,
    aws_iam_role_policy_attachment.gpu_node_AmazonEC2ContainerRegistryReadOnly,
  ]
}

# Launch Template for Training Nodes
resource "aws_launch_template" "gpu_training" {
  name_prefix = "${var.cluster_name}-gpu-training-"
  description = "Launch template for GPU training nodes"

  block_device_mappings {
    device_name = "/dev/xvda"

    ebs {
      volume_size           = 200  # 200GB for models and datasets
      volume_type           = "gp3"
      iops                  = 3000
      throughput            = 125
      delete_on_termination = true
      encrypted             = true
    }
  }

  metadata_options {
    http_endpoint               = "enabled"
    http_tokens                 = "required"
    http_put_response_hop_limit = 1
    instance_metadata_tags      = "enabled"
  }

  monitoring {
    enabled = true
  }

  tag_specifications {
    resource_type = "instance"
    tags = {
      Name    = "${var.cluster_name}-gpu-training"
      Workload = "ML-Training"
    }
  }

  user_data = base64encode(templatefile("${path.module}/user-data.sh", {
    cluster_name        = data.aws_eks_cluster.main.name
    nvidia_driver_version = var.nvidia_driver_version
  }))

  lifecycle {
    create_before_destroy = true
  }
}

# Launch Template for Serving Nodes
resource "aws_launch_template" "gpu_serving" {
  name_prefix = "${var.cluster_name}-gpu-serving-"
  description = "Launch template for GPU serving nodes"

  block_device_mappings {
    device_name = "/dev/xvda"

    ebs {
      volume_size           = 100  # 100GB for serving
      volume_type           = "gp3"
      iops                  = 3000
      throughput            = 125
      delete_on_termination = true
      encrypted             = true
    }
  }

  metadata_options {
    http_endpoint               = "enabled"
    http_tokens                 = "required"
    http_put_response_hop_limit = 1
    instance_metadata_tags      = "enabled"
  }

  monitoring {
    enabled = true
  }

  tag_specifications {
    resource_type = "instance"
    tags = {
      Name     = "${var.cluster_name}-gpu-serving"
      Workload = "ML-Serving"
    }
  }

  user_data = base64encode(templatefile("${path.module}/user-data.sh", {
    cluster_name          = data.aws_eks_cluster.main.name
    nvidia_driver_version = var.nvidia_driver_version
  }))

  lifecycle {
    create_before_destroy = true
  }
}

# IAM Role for GPU Nodes
resource "aws_iam_role" "gpu_node_role" {
  name               = "${var.cluster_name}-gpu-node-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = {
        Service = "ec2.amazonaws.com"
      }
      Action = "sts:AssumeRole"
    }]
  })

  tags = {
    Name = "${var.cluster_name}-gpu-node-role"
  }
}

# IAM Policy Attachments
resource "aws_iam_role_policy_attachment" "gpu_node_AmazonEKSWorkerNodePolicy" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSWorkerNodePolicy"
  role       = aws_iam_role.gpu_node_role.name
}

resource "aws_iam_role_policy_attachment" "gpu_node_AmazonEKS_CNI_Policy" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKS_CNI_Policy"
  role       = aws_iam_role.gpu_node_role.name
}

resource "aws_iam_role_policy_attachment" "gpu_node_AmazonEC2ContainerRegistryReadOnly" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly"
  role       = aws_iam_role.gpu_node_role.name
}

# Additional policy for SSM access
resource "aws_iam_role_policy_attachment" "gpu_node_AmazonSSMManagedInstanceCore" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
  role       = aws_iam_role.gpu_node_role.name
}

# Outputs
output "gpu_training_node_group_id" {
  description = "ID of the GPU training node group"
  value       = aws_eks_node_group.gpu_training.id
}

output "gpu_serving_node_group_id" {
  description = "ID of the GPU serving node group"
  value       = aws_eks_node_group.gpu_serving.id
}

output "gpu_node_role_arn" {
  description = "ARN of the GPU node IAM role"
  value       = aws_iam_role.gpu_node_role.arn
}
