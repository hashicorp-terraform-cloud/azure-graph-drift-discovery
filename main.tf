terraform {
  required_providers {
    msgraph = {
      source = "microsoft/msgraph"
    }
    azuread = {
      source = "hashicorp/azuread"
    }
  }
}

provider "msgraph" {
}

provider "azuread" {
}
