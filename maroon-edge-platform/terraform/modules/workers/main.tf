variable "name"            { type = string }
variable "vpc_id"          { type = string }
variable "private_subnets" { type = list(string) }

resource "aws_ecs_cluster" "workers" {
  name = "${var.name}-workers"
}

resource "aws_iam_role" "worker_role" {
  name = "${var.name}-worker-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = { Service = "ecs-tasks.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "worker_route53" {
  role       = aws_iam_role.worker_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonRoute53FullAccess"
}

output "worker_cluster_id" {
  value = aws_ecs_cluster.workers.id
}
