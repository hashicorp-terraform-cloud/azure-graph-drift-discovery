output "entra_group" {
  value = azuread_group.group
}

output "entra_users" {
  value = [for user in azuread_user.user : user.user_principal_name]
}
