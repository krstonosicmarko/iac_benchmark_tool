provider "aws" {
  region = "eu-north-1"  # or your preferred region
}

resource "aws_s3_bucket" "s3-bucket-benchmark" {
  bucket = "s3-bucket-benchmark-mk-23042025"  # replace with unique name
}

output "bucket_name" {
  value = aws_s3_bucket.s3-bucket-benchmark.bucket
}

output "bucket_region" {
  value = aws_s3_bucket.s3-bucket-benchmark.region
}