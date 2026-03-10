provider "aws" {
  region = "eu-central-1"
}

# SCALING CONTROL: Change this number for different scenarios
variable "resource_count" {
  description = "Number of EC2 instances to create"
  type        = number
  default     = 10  # Change to 10 or 25 for scaling scenarios
}

# Generate random suffix for unique names
resource "random_id" "instance_suffix" {
  byte_length = 4
}

# Get the latest Amazon Linux 2 AMI
data "aws_ami" "amazon_linux" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["amzn2-ami-hvm-*-x86_64-gp2"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

# EC2 instances with scaling support
resource "aws_instance" "basic_instances" {
  count         = var.resource_count
  ami           = data.aws_ami.amazon_linux.id
  instance_type = "t3.micro"

  tags = {
    Name        = "test-basic-instance-${count.index}-${random_id.instance_suffix.hex}"
    Environment = "test"
    Purpose     = "benchmarking"
    Index       = count.index
  }
}

# Outputs for validation - handles multiple instances
output "instance_ids" {
  value       = aws_instance.basic_instances[*].id
  description = "IDs of the created EC2 instances"
}

output "instance_count" {
  value       = length(aws_instance.basic_instances)
  description = "Number of instances created"
}

output "instance_public_ips" {
  value       = aws_instance.basic_instances[*].public_ip
  description = "Public IP addresses of the EC2 instances"
}