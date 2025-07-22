provider "aws" {
  region = "eu-north-1"
}

resource "aws_s3_bucket" "test-bucket" {
  bucket = "test-bucket-mk-${random_id.bucket_suffix.hex}" 
}

resource "random_id" "bucket_suffix" {
  byte_length = 4
}

output "bucket_name" {
  value = aws_s3_bucket.test-bucket.bucket
}

output "bucket_region" {
  value = aws_s3_bucket.test-bucket.region
}
