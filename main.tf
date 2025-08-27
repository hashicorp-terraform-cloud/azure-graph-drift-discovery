terraform {
  required_providers {
    msgraph = {
      source = "microsoft/msgraph"
    }
  }
}

provider "msgraph" {
}


resource "msgraph_resource" "group" {
  url = "groups"
  body = {
    displayName     = "Drift Demo Group"
    mailEnabled     = false
    mailNickname    = "driftdemo"
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

output "all" {
  value = data.msgraph_resource.group.output.all
}
