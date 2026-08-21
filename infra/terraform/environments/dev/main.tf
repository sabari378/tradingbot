terraform { required_version = ">= 1.6" }
variable "aws_region" { type = string, default = "us-east-1" }
variable "environment" { type = string, default = "dev" }
# Remote state, VPC, EKS, RDS, Redis, ECR, IAM, Secrets Manager and CloudWatch modules attach here.
