variable "name"            { type = string }
variable "vpc_id"          { type = string }
variable "private_subnets" { type = list(string) }

resource "aws_ecs_cluster" "control_plane" {
  name = "${var.name}-control-plane"
}

resource "aws_s3_bucket" "templates" {
  bucket = "${var.name}-sovereign-templates"
}

output "control_plane_cluster_id" {
  value = aws_ecs_cluster.control_plane.id
}
output "templates_bucket" {
  value = aws_s3_bucket.templates.bucket
}
