variable "name" { type = string }

resource "aws_vpc" "this" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_support   = true
  enable_dns_hostnames = true
  tags = { Name = "${var.name}-vpc" }
}

resource "aws_subnet" "public_1" {
  vpc_id                  = aws_vpc.this.id
  cidr_block              = "10.0.1.0/24"
  map_public_ip_on_launch = true
  availability_zone       = "us-west-2a"
  tags = { Name = "${var.name}-public-1" }
}

resource "aws_subnet" "private_1" {
  vpc_id            = aws_vpc.this.id
  cidr_block        = "10.0.2.0/24"
  availability_zone = "us-west-2a"
  tags = { Name = "${var.name}-private-1" }
}

output "vpc_id" { 
  value = aws_vpc.this.id 
}
output "public_subnets" { 
  value = [aws_subnet.public_1.id] 
}
output "private_subnets" { 
  value = [aws_subnet.private_1.id] 
}
