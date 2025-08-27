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


// tests with the msgraph provider

resource "msgraph_resource" "group" {
  url = "groups"
  body = {
    displayName     = "${var.group_base_name} - MSGraph"
    mailEnabled     = false
    mailNickname    = "msgraph"
    securityEnabled = true
  }
}

data "msgraph_resource" "group" {
  url = "groups/${msgraph_resource.group.id}"
  response_export_values = {
    all          = "@"
    display_name = "displayName"
  }
}

output "msgraph_all" {
  value = data.msgraph_resource.group.output.all
}


// tests with the azuread provider

resource "azuread_group" "group" {
  display_name     = "${var.group_base_name} - AzureAD"
  mail_enabled     = false
  mail_nickname    = "azuread"
  security_enabled = true
}
