check "check_group_memberships" {
  data "azuread_group" "managed_group" {
    display_name = var.group_base_name
  }

  assert {
    condition     = length(data.azuread_group.managed_group.members) == length(azuread_user.user)
    error_message = "${length(data.azuread_group.managed_group.members)} users exist in the group, but ${length(azuread_user.user)} users are managed by Terraform"
  }
}
