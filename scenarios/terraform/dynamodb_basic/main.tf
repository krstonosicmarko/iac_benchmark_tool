provider "aws" {
  region = "eu-north-1"
}

resource "aws_dynamodb_table" "dynamodb-table-basic" {
  name           = "dynamodb-table-basic-mk"
  billing_mode   = "PROVISIONED"
  read_capacity  = 1
  write_capacity = 1
  hash_key       = "id"
  
  attribute {
    name = "id"
    type = "S"
  }
  
  tags = {
    Name = "dynamodb-table-basic"
  }
}

output "table_name" {
  value = aws_dynamodb_table.dynamodb-table-basic.name
}

output "table_arn" {
  value = aws_dynamodb_table.dynamodb-table-basic.arn
}