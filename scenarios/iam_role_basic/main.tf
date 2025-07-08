provider "aws" {
  region = "eu-north-1"
}

resource "aws_iam_role" "iam-role-test" {
  name = "benchmark-test-role"

  assume_role_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "ec2.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF
}

output "role_arn" {
  value = aws_iam_role.iam-role-test.arn
}

output "role_name" {
  value = aws_iam_role.iam-role-test.name
}