check "check_managed_users" {
  data "azuread_users" "all_users" { return_all = true }

  assert {
    condition     = length(data.azuread_users.all_users.user_principal_names) == length(azuread_user.user)
    error_message = "${length(data.azuread_users.all_users.user_principal_names)} users exist, but ${length(azuread_user.user)} users are managed by Terraform"
  }
}

check "check_group_memberships" {
  data "azuread_group" "managed_group" {
    display_name = var.group_base_name
  }

  assert {
    condition     = length(data.azuread_group.managed_group.members) == length(azuread_user.user)
    error_message = "${length(data.azuread_group.managed_group.members)} users exist in the group, but ${length(azuread_user.user)} users are managed by Terraform"
  }
}
