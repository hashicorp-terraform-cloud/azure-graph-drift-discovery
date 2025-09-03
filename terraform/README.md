# Entra Drift Discovery 
Small Terraform project to provide the basis for demonstrating drift on Entra resources managed by the AzureAD provider in Terraform.

<!-- BEGIN_TF_DOCS -->
## Requirements

No requirements.

## Providers

| Name | Version |
|------|---------|
| <a name="provider_azuread"></a> [azuread](#provider\_azuread) | 3.5.0 |
| <a name="provider_random"></a> [random](#provider\_random) | 3.7.2 |

## Modules

No modules.

## Resources

| Name | Type |
|------|------|
| [azuread_group.group](https://registry.terraform.io/providers/hashicorp/azuread/latest/docs/resources/group) | resource |
| [azuread_group_member.member](https://registry.terraform.io/providers/hashicorp/azuread/latest/docs/resources/group_member) | resource |
| [azuread_user.user](https://registry.terraform.io/providers/hashicorp/azuread/latest/docs/resources/user) | resource |
| [random_password.password](https://registry.terraform.io/providers/hashicorp/random/latest/docs/resources/password) | resource |

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| <a name="input_domain_name"></a> [domain\_name](#input\_domain\_name) | Domain for the user to be associated with | `string` | `"onmi.cloud"` | no |
| <a name="input_group_base_name"></a> [group\_base\_name](#input\_group\_base\_name) | Base Display name for the Entra group | `string` | `"Entra Drift Demo"` | no |
| <a name="input_username"></a> [username](#input\_username) | Username for the Entra user | `string` | `"demo.user"` | no |

## Outputs

| Name | Description |
|------|-------------|
| <a name="output_entra_group"></a> [entra\_group](#output\_entra\_group) | n/a |
| <a name="output_entra_user"></a> [entra\_user](#output\_entra\_user) | n/a |
<!-- END_TF_DOCS -->