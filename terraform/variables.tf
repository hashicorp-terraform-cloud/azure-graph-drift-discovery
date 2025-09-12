// azuread provider variables
variable "group_base_name" {
  type        = string
  description = "Base Display name for the Entra group"
  default     = "Entra Drift Demo"
}

variable "users" {
  description = "Set of usernames to create"
  type        = set(string)
}

variable "domain_name" {
  type        = string
  description = "Domain for the user to be associated with"
  default     = "onmi.cloud"
}
