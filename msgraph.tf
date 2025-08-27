// invite b2b user with msgraph provider

resource "msgraph_resource" "b2b_user" {
  url = "invitations"
  body = {
    "invitedUserEmailAddress" : "${var.b2b_email}",
    "inviteRedirectUrl" : "${var.b2b_invite_redirect_url}"
  }
  response_export_values = {
    all = "@"
  }
}


