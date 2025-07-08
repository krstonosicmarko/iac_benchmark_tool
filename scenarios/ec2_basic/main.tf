provider "aws" {
  region = "eu-north-1"
}

resource "aws_instance" "test_instance" {
  ami           = "ami-006b4a3ad5f56fbd6"  
  instance_type = "t3.micro"              
  
  tags = {
    Name = "test-instance-mk"
  }
}

output "instance_id" {
  value = aws_instance.test_instance.id
}

output "instance_public_ip" {
  value = aws_instance.test_instance.public_ip
}