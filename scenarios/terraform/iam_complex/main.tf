# IAM Complex Scenario - Terraform Implementation
# Role + 1 custom policy attachment (scaled down from user/group complexity)

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
resource "random_id" "iam_suffix" {
  byte_length = 4
}

# IAM Role Trust Policy - allows EC2 to assume this role
data "aws_iam_policy_document" "assume_role_policy" {
  statement {
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["ec2.amazonaws.com"]
    }

    actions = ["sts:AssumeRole"]
  }
}

# Custom IAM Policy for S3 read-only access
data "aws_iam_policy_document" "s3_readonly_policy" {
  statement {
    effect = "Allow"

    actions = [
      "s3:GetObject",
      "s3:ListBucket"
    ]

    resources = [
      "arn:aws:s3:::*",
      "arn:aws:s3:::*/*"
    ]
  }
}

# IAM Role
resource "aws_iam_role" "complex_role" {
  name               = "iam-complex-role-${random_id.iam_suffix.hex}"
  assume_role_policy = data.aws_iam_policy_document.assume_role_policy.json

  tags = {
    Name        = "iam-complex-role-${random_id.iam_suffix.hex}"
    Environment = "test"
    Purpose     = "benchmarking"
  }
}

# Custom IAM Policy
resource "aws_iam_policy" "s3_readonly_policy" {
  name        = "iam-complex-s3-readonly-${random_id.iam_suffix.hex}"
  path        = "/"
  description = "Custom S3 read-only policy for benchmarking"

  policy = data.aws_iam_policy_document.s3_readonly_policy.json

  tags = {
    Name        = "iam-complex-s3-readonly-${random_id.iam_suffix.hex}"
    Environment = "test"
    Purpose     = "benchmarking"
  }
}

# Attach custom policy to role
resource "aws_iam_role_policy_attachment" "complex_policy_attachment" {
  role       = aws_iam_role.complex_role.name
  policy_arn = aws_iam_policy.s3_readonly_policy.arn
}

# Instance profile to use the role with EC2 (common pattern)
resource "aws_iam_instance_profile" "complex_instance_profile" {
  name = "iam-complex-profile-${random_id.iam_suffix.hex}"
  role = aws_iam_role.complex_role.name

  tags = {
    Name        = "iam-complex-profile-${random_id.iam_suffix.hex}"
    Environment = "test"
    Purpose     = "benchmarking"
  }
}

# Outputs for validation
output "role_name" {
  value       = aws_iam_role.complex_role.name
  description = "Name of the IAM role"
}

output "role_arn" {
  value       = aws_iam_role.complex_role.arn
  description = "ARN of the IAM role"
}

output "policy_name" {
  value       = aws_iam_policy.s3_readonly_policy.name
  description = "Name of the custom IAM policy"
}

output "policy_arn" {
  value       = aws_iam_policy.s3_readonly_policy.arn
  description = "ARN of the custom IAM policy"
}

output "instance_profile_name" {
  value       = aws_iam_instance_profile.complex_instance_profile.name
  description = "Name of the IAM instance profile"
}