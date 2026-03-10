provider "aws" {
  region = "eu-central-1"
}

variable "resource_count" {
  description = "Number of S3 buckets to create"
  type        = number
  default     = 1
}

resource "random_id" "bucket_suffix" {
  byte_length = 4
}

resource "aws_s3_bucket" "basic_buckets" {
  count  = var.resource_count
  bucket = "test-basic-bucket-mk-${count.index}-${random_id.bucket_suffix.hex}"

  tags = {
    Name        = "test-basic-bucket-${count.index}"
    Environment = "test"
    Purpose     = "benchmarking"
    Index       = count.index
  }
}

output "bucket_names" {
  value       = aws_s3_bucket.basic_buckets[*].id
}

output "bucket_count" {
  value       = length(aws_s3_bucket.basic_buckets)
}

output "bucket_region" {
  value       = aws_s3_bucket.basic_buckets[0].region
}