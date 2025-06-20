provider "aws" {
  region = "eu-north-1"
}

resource "aws_s3_bucket" "test-bucket" {
  bucket = "test-bucket-mk-${random_id.bucket_suffix.hex}" 
}

resource "random_id" "bucket_suffix" {
  byte_length = 4
}

resource "aws_instance" "test_instance" {
  ami           = "ami-006b4a3ad5f56fbd6"  
  instance_type = "t3.micro"              
  
  tags = {
    Name = "test-instance-mk"
  }
}

output "bucket_name" {
  value = aws_s3_bucket.test-bucket.bucket
}

output "bucket_region" {
  value = aws_s3_bucket.test-bucket.region
}

output "instance_id" {
  value = aws_instance.test_instance.id
}

output "instance_public_ip" {
  value = aws_instance.test_instance.public_ip
}