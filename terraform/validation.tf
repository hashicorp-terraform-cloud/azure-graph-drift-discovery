check "check_managed_users" {
  data "azuread_users" "all_users" {}

  assert {
    condition     = length(data.azuread_users.all_users) == length(azuread_user.user)
    error_message = "${length(data.azuread_users.all_users)} users exist, but ${length(azuread_user.user)} users are managed by Terraform"
  }
}

check "check_group_memberships" {
  data "azure_ad_group" "managed_group" {
    display_name = var.group_base_name
  }

  assert {
    condition     = length(data.azure_ad_group.managed_group.members) == length(azuread_user.user)
    error_message = "${length(data.azure_ad_group.managed_group.members)} users exist in the group, but ${length(azuread_user.user)} users are managed by Terraform"
  }
}
