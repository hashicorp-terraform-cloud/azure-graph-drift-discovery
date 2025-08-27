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
