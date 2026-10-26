terraform { required_version = ">= 1.6" }
variable "aws_region" { type = string }
variable "environment" { type = string, default = "prod" }
