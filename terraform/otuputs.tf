output "entra_group" {
  value = azuread_group.group
}

output "entra_user" {
  value = azuread_user.user.display_name
}
