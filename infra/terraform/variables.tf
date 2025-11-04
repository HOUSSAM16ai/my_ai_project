# Terraform Variables for GPU Node Groups

variable "aws_region" {
  description = "AWS region for resources"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "prod"
}

variable "cluster_name" {
  description = "EKS cluster name"
  type        = string
}

variable "private_subnet_ids" {
  description = "List of private subnet IDs for node groups"
  type        = list(string)
}

# GPU Training Node Group
variable "gpu_training_min_size" {
  description = "Minimum number of GPU training nodes"
  type        = number
  default     = 0
}

variable "gpu_training_desired_size" {
  description = "Desired number of GPU training nodes"
  type        = number
  default     = 1
}

variable "gpu_training_max_size" {
  description = "Maximum number of GPU training nodes"
  type        = number
  default     = 10
}

# GPU Serving Node Group
variable "gpu_serving_min_size" {
  description = "Minimum number of GPU serving nodes"
  type        = number
  default     = 1
}

variable "gpu_serving_desired_size" {
  description = "Desired number of GPU serving nodes"
  type        = number
  default     = 2
}

variable "gpu_serving_max_size" {
  description = "Maximum number of GPU serving nodes"
  type        = number
  default     = 10
}

# Cost Optimization
variable "use_spot_instances" {
  description = "Use spot instances for training nodes"
  type        = bool
  default     = true
}

# NVIDIA Driver
variable "nvidia_driver_version" {
  description = "NVIDIA driver version to install"
  type        = string
  default     = "535.129.03"
}
