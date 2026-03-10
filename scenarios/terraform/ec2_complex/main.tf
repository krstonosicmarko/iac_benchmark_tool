provider "aws" {
  region = "eu-central-1"
}

# SCALING CONTROL: Change this number for different scenarios
variable "resource_count" {
  description = "Number of complex EC2 instances to create"
  type        = number
  default     = 10  # Change to 10 for scaling scenario
}

# Generate random suffix for unique names
resource "random_id" "instance_suffix" {
  byte_length = 4
}

# Get default VPC
data "aws_vpc" "default" {
  default = true
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

# Simple security group for all instances (complexity feature)
resource "aws_security_group" "complex_sg" {
  name_prefix = "ec2-complex-sg-${random_id.instance_suffix.hex}"
  vpc_id      = data.aws_vpc.default.id

  # Allow SSH access
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["10.0.0.0/8"] # Restrictive for security
  }

  # Allow all outbound traffic
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "ec2-complex-sg-${random_id.instance_suffix.hex}"
    Environment = "test"
    Purpose     = "benchmarking"
  }
}

# EC2 instances with security group (complexity)
resource "aws_instance" "complex_instances" {
  count                  = var.resource_count
  ami                    = data.aws_ami.amazon_linux.id
  instance_type          = "t3.micro"
  vpc_security_group_ids = [aws_security_group.complex_sg.id]

  tags = {
    Name        = "test-complex-instance-${count.index}-${random_id.instance_suffix.hex}"
    Environment = "test"
    Purpose     = "benchmarking"
    Index       = count.index
  }
}

# Outputs for validation - handles multiple instances
output "instance_ids" {
  value       = aws_instance.complex_instances[*].id
  description = "IDs of the created EC2 instances"
}

output "instance_count" {
  value       = length(aws_instance.complex_instances)
  description = "Number of complex instances created"
}

output "instance_public_ips" {
  value       = aws_instance.complex_instances[*].public_ip
  description = "Public IP addresses of the EC2 instances"
}

output "security_group_id" {
  value       = aws_security_group.complex_sg.id
  description = "ID of the shared security group"
}

output "features_enabled" {
  value = {
    security_group = "Custom SSH-only security group"
    instance_type  = "t3.micro"
  }
  description = "Complex features enabled for all instances"
}