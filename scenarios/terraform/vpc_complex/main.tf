# VPC Complex Scenario - Terraform Implementation
# VPC + 2 subnets + internet gateway (scaled down from NAT gateway and route tables)

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = "eu-central-1"
}

# Generate random suffix for unique names
resource "random_id" "vpc_suffix" {
  byte_length = 4
}

# VPC
resource "aws_vpc" "complex_vpc" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name        = "vpc-complex-${random_id.vpc_suffix.hex}"
    Environment = "test"
    Purpose     = "benchmarking"
  }
}

# Internet Gateway
resource "aws_internet_gateway" "complex_igw" {
  vpc_id = aws_vpc.complex_vpc.id

  tags = {
    Name        = "igw-complex-${random_id.vpc_suffix.hex}"
    Environment = "test"
    Purpose     = "benchmarking"
  }
}

# First subnet (public)
resource "aws_subnet" "complex_subnet_1" {
  vpc_id            = aws_vpc.complex_vpc.id
  cidr_block        = "10.0.1.0/24"
  availability_zone = data.aws_availability_zones.available.names[0]

  map_public_ip_on_launch = true

  tags = {
    Name        = "subnet-complex-1-${random_id.vpc_suffix.hex}"
    Environment = "test"
    Purpose     = "benchmarking"
    Type        = "public"
  }
}

# Second subnet (public)
resource "aws_subnet" "complex_subnet_2" {
  vpc_id            = aws_vpc.complex_vpc.id
  cidr_block        = "10.0.2.0/24"
  availability_zone = data.aws_availability_zones.available.names[1]

  map_public_ip_on_launch = true

  tags = {
    Name        = "subnet-complex-2-${random_id.vpc_suffix.hex}"
    Environment = "test"
    Purpose     = "benchmarking"
    Type        = "public"
  }
}

# Route table for public subnets
resource "aws_route_table" "complex_public_rt" {
  vpc_id = aws_vpc.complex_vpc.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.complex_igw.id
  }

  tags = {
    Name        = "rt-public-complex-${random_id.vpc_suffix.hex}"
    Environment = "test"
    Purpose     = "benchmarking"
  }
}

# Associate route table with first subnet
resource "aws_route_table_association" "complex_public_rta_1" {
  subnet_id      = aws_subnet.complex_subnet_1.id
  route_table_id = aws_route_table.complex_public_rt.id
}

# Associate route table with second subnet
resource "aws_route_table_association" "complex_public_rta_2" {
  subnet_id      = aws_subnet.complex_subnet_2.id
  route_table_id = aws_route_table.complex_public_rt.id
}

# Data source for availability zones
data "aws_availability_zones" "available" {
  state = "available"
}

# Outputs for validation
output "vpc_id" {
  value       = aws_vpc.complex_vpc.id
  description = "ID of the VPC"
}

output "vpc_cidr" {
  value       = aws_vpc.complex_vpc.cidr_block
  description = "CIDR block of the VPC"
}

output "internet_gateway_id" {
  value       = aws_internet_gateway.complex_igw.id
  description = "ID of the Internet Gateway"
}

output "subnet_1_id" {
  value       = aws_subnet.complex_subnet_1.id
  description = "ID of the first subnet"
}

output "subnet_1_cidr" {
  value       = aws_subnet.complex_subnet_1.cidr_block
  description = "CIDR block of the first subnet"
}

output "subnet_2_id" {
  value       = aws_subnet.complex_subnet_2.id
  description = "ID of the second subnet"
}

output "subnet_2_cidr" {
  value       = aws_subnet.complex_subnet_2.cidr_block
  description = "CIDR block of the second subnet"
}