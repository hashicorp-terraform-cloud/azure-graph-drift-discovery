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
