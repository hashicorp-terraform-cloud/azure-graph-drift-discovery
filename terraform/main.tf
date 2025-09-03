terraform {
  required_providers {
    msgraph = {
      source = "microsoft/msgraph"
    }
    azuread = {
      source = "hashicorp/azuread"
    }
    random = {
      source = "hashicorp/random"
    }
  }
}

provider "msgraph" {
}

provider "azuread" {
}

provider "random" {
}
