// create a group and user with the azuread provider
resource "azuread_group" "group" {
  display_name     = var.group_base_name
  description      = "Managed by Terraform - AzureAD Provider"
  mail_enabled     = false
  mail_nickname    = "azuread"
  security_enabled = true
}

resource "random_password" "password" {
  length  = 16
  special = false
}

resource "azuread_user" "user" {
  user_principal_name = "${var.username}@${var.domain_name}"
  display_name        = var.username
  mail_nickname       = var.username
  password            = random_password.password.result
}

// add the user to the group
resource "azuread_group_member" "member" {
  group_object_id  = azuread_group.group.object_id
  member_object_id = azuread_user.user.object_id
}
