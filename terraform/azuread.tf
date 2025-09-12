// create a group and user with the azuread provider
resource "azuread_group" "group" {
  display_name     = var.group_base_name
  description      = "Managed by Terraform - AzureAD Provider"
  mail_enabled     = false
  security_enabled = true
}

# Create a random password for each user
resource "random_password" "password" {
  for_each = var.users

  length           = 32
  lower            = true
  upper            = true
  special          = true
  numeric          = true
  override_special = "-._~"
}

# Create each user
resource "azuread_user" "user" {
  for_each = var.users

  user_principal_name = "${each.value}@${var.domain_name}"
  display_name        = each.value
  mail_nickname       = each.value
  password            = random_password.password[each.key].result
}

# Add each user to the group
resource "azuread_group_member" "member" {
  for_each = var.users

  group_object_id  = azuread_group.group.object_id
  member_object_id = azuread_user.user[each.key].object_id
}
