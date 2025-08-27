// azuread provider variables
variable "group_base_name" {
  type        = string
  description = "Base Display name for the Entra group"
  default     = "Entra Drift Demo"
}

variable "username" {
  type        = string
  description = "Username for the Entra user"
  default     = "demo.user"
}

variable "domain_name" {
  type        = string
  description = "Domain for the user to be associated with"
  default     = "onmi.cloud"
}
