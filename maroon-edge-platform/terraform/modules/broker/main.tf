variable "name"            { type = string }
variable "vpc_id"          { type = string }
variable "private_subnets" { type = list(string) }
variable "broker_sg_id"    { type = string }

resource "aws_dynamodb_table" "requests" {
  name         = "${var.name}-broker-requests"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "id"

  attribute {
    name = "id"
    type = "S"
  }
}

resource "aws_sqs_queue" "provisioning" {
  name = "${var.name}-provisioning-queue"
}

output "broker_queue_url" {
  value = aws_sqs_queue.provisioning.url
}

output "broker_table_name" {
  value = aws_dynamodb_table.requests.name
}
