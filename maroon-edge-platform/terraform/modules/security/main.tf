variable "name" { type = string }

resource "aws_security_group" "broker" {
  name        = "${var.name}-broker-sg"
  description = "Security Group for Broker ECS tasks"

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

output "broker_sg_id" {
  value = aws_security_group.broker.id
}
