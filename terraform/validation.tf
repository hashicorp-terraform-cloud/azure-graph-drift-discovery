check "verify_group_membership" {
  data "azuread_group" "managed_group" {
    display_name = var.group_base_name
  }

  assert {
    condition     = length(data.azuread_group.managed_group.members) == length(azuread_user.user)
    error_message = "${length(data.azuread_group.managed_group.members)} users exist in the group, but ${length(azuread_user.user)} users are managed by Terraform"
  }

  assert {
    condition = length([
      for user_key, user in azuread_user.user :
      user.user_principal_name
      if !contains(data.azuread_group.managed_group.members, user.object_id)
    ]) == 0
    error_message = "The following Terraform-managed users are missing from the group: ${join(", ", [
      for user_key, user in azuread_user.user :
      user.user_principal_name
      if !contains(data.azuread_group.managed_group.members, user.object_id)
    ])}"
  }

  assert {
    condition = length([
      for member_id in data.azuread_group.managed_group.members :
      member_id
      if !contains(values(azuread_user.user)[*].object_id, member_id)
    ]) == 0
    error_message = "The following users are in the group but not managed by Terraform (IDs): ${join(", ", [
      for member_id in data.azuread_group.managed_group.members :
      member_id
      if !contains(values(azuread_user.user)[*].object_id, member_id)
    ])}"
  }
}
