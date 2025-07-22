provider "aws" {
  region = "eu-north-1"
}

resource "aws_vpc" "vpc-basic" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true
  
  tags = {
    Name = "benchmark-vpc-basic"
  }
}

resource "aws_subnet" "vpc-basic" {
  vpc_id                  = aws_vpc.vpc-basic.id
  cidr_block              = "10.0.1.0/24"
  availability_zone       = "eu-north-1a"
  
  tags = {
    Name = "benchmark-subnet-basic"
  }
}

output "vpc_id" {
  value = aws_vpc.vpc-basic
}

output "vpc_cidr" {
  value = aws_vpc.vpc-basic.cidr_block
}

output "subnet_id" {
  value = aws_subnet.vpc-basic.id
}

output "subnet_cidr" {
  value = aws_subnet.vpc-basic.cidr_block
}