variable "aws_region" {
  type        = string
  description = "AWS deployment region"
  default     = "us-east-1"
}

variable "environment" {
  type        = string
  description = "Environment name"
  default     = "sandbox"
}

variable "vpc_cidr" {
  type        = string
  description = "Private VPC IPv4 range"
  default     = "10.42.0.0/16"
}

variable "db_name" {
  type    = string
  default = "finsphere"
}

variable "db_username" {
  type    = string
  default = "finsphere_app"
}

variable "db_password" {
  type        = string
  sensitive   = true
  description = "Pass through a secret manager or secure CI variable; never commit a tfvars file."
}

variable "application_security_group_id" {
  type        = string
  description = "Security group attached to the application nodes/tasks in this VPC."
}
