terraform {
  required_version = ">= 1.7.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = "us-west-2"
}

module "network" {
  source = "../../modules/network"
  name   = "root-dev"
}

module "security" {
  source = "../../modules/security"
  name   = "root-dev"
}

module "broker" {
  source          = "../../modules/broker"
  name            = "root-dev"
  vpc_id          = module.network.vpc_id
  private_subnets = module.network.private_subnets
  broker_sg_id    = module.security.broker_sg_id
}

module "workers" {
  source          = "../../modules/workers"
  name            = "root-dev"
  vpc_id          = module.network.vpc_id
  private_subnets = module.network.private_subnets
}

module "control_plane" {
  source          = "../../modules/control_plane"
  name            = "root-dev"
  vpc_id          = module.network.vpc_id
  private_subnets = module.network.private_subnets
}

module "envoy_fleet" {
  source          = "../../modules/envoy_fleet"
  name            = "root-dev"
  vpc_id          = module.network.vpc_id
  public_subnets  = module.network.public_subnets
  private_subnets = module.network.private_subnets
}

module "observability" {
  source = "../../modules/observability"
  name   = "root-dev"
}
