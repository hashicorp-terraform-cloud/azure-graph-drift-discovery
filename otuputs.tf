output "entra_group" {
  value = azuread_group.group
}

output "entra_user" {
  value = azuread_user.user
}

output "b2b_invitation" {
  value = msgraph_resource.b2b_user.output.all
}
