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

// assign the group to the built-in Reader role
resource "azuread_directory_role" "role" {
  display_name = "Reader"
}

resource "azuread_directory_role_assignment" "assignment" {
  role_id             = azuread_directory_role.role.template_id
  principal_object_id = azuread_group.group.object_id
}

// lets invite a b2b user to the directory
resource "azuread_invitation" "b2b" {
  user_email_address = var.b2b_email
  redirect_url       = var.b2b_invite_redirect_url

  message {
    body = "Hello there! You are invited to join the ${var.domain_name} Azure tenant!"
  }
}
