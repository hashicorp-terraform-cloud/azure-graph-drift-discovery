output "msgraph_group_display_name" {
  value = data.msgraph_resource.group.output.display_name
}

output "azuread_group_display_name" {
  value = azuread_group.group.display_name
}
