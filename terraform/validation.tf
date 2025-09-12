check "verify_group_membership" {
  data "azuread_group" "managed_group" {
    display_name = var.group_base_name
  }

  assert {
    condition     = length(data.azuread_group.managed_group.members) == length(azuread_user.user)
    error_message = "${length(data.azuread_group.managed_group.members)} users exist in the group, but ${length(azuread_user.user)} users are managed by Terraform"
  }

  assert {
    condition = alltrue([
      for user_key, user in azuread_user.user :
      contains(data.azuread_group.managed_group.members, user.object_id)
    ])
    error_message = "Not all Terraform-managed users are present in the group membership list"
  }
}
