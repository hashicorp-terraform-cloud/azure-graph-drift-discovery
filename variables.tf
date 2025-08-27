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

//msgraogh provider variables
variable "b2b_email" {
  type        = string
  description = "Email address for the B2B user to be invited"
  default     = ""
}

variable "b2b_invite_redirect_url" {
  type        = string
  description = "Redirect URL for the B2B user to be invited"
  default     = "https://welcome.onmi.cloud"
}
