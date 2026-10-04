output "vpc_id" {
  value = aws_vpc.main.id
}

output "private_subnet_ids" {
  value = aws_subnet.private[*].id
}

output "database_endpoint" {
  value = aws_db_instance.main.address
}

output "database_security_group_id" {
  value = aws_security_group.database.id
}
