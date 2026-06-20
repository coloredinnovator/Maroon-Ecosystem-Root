variable "name"            { type = string }
variable "vpc_id"          { type = string }
variable "public_subnets"  { type = list(string) }
variable "private_subnets" { type = list(string) }

resource "aws_lb" "envoy" {
  name               = "${var.name}-envoy-lb"
  internal           = false
  load_balancer_type = "network"
  subnets            = var.public_subnets
}

resource "aws_lb_target_group" "envoy" {
  name     = "${var.name}-envoy-tg"
  port     = 443
  protocol = "TCP"
  vpc_id   = var.vpc_id
}

resource "aws_lb_listener" "envoy_https" {
  load_balancer_arn = aws_lb.envoy.arn
  port              = "443"
  protocol          = "TCP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.envoy.arn
  }
}

# Auto Scaling Group placeholder for AMI baked with Packer
resource "aws_launch_template" "envoy" {
  name_prefix   = "${var.name}-envoy-"
  image_id      = "ami-placeholder" # Will be updated via Packer/SSM
  instance_type = "t3.medium"
}

output "envoy_lb_dns" {
  value = aws_lb.envoy.dns_name
}
