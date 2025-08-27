// tests with the azuread provider
resource "azuread_group" "group" {
  display_name     = "${var.group_base_name} - AzureAD"
  mail_enabled     = false
  mail_nickname    = "azuread"
  security_enabled = true
}

resource "azuread_user" "user" {
  user_principal_name = "user@app.terraform.io"
  display_name        = "User ${var.group_base_name} - AzureAD"
  mail_nickname       = "user"
  password            = "P@ssword1234"
}

resource "azuread_group_member" "member" {
  group_object_id  = azuread_group.group.object_id
  member_object_id = azuread_user.user.object_id
}

resource "azuread_directory_role" "role" {
  display_name = "Reader"
}

resource "azuread_directory_role_assignment" "assignment" {
  role_id             = azuread_directory_role.role.template_id
  principal_object_id = azuread_group.group.object_id
}
