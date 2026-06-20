variable "name" { type = string }

resource "aws_cloudwatch_log_group" "broker" {
  name              = "/ecs/${var.name}-broker"
  retention_in_days = 14
}

resource "aws_cloudwatch_log_group" "worker" {
  name              = "/ecs/${var.name}-worker"
  retention_in_days = 14
}

resource "aws_cloudwatch_log_group" "control_plane" {
  name              = "/ecs/${var.name}-control-plane"
  retention_in_days = 14
}

resource "aws_cloudwatch_log_group" "envoy" {
  name              = "/ec2/${var.name}-envoy"
  retention_in_days = 14
}

output "log_groups" {
  value = [
    aws_cloudwatch_log_group.broker.name,
    aws_cloudwatch_log_group.worker.name,
    aws_cloudwatch_log_group.control_plane.name,
    aws_cloudwatch_log_group.envoy.name,
  ]
}
