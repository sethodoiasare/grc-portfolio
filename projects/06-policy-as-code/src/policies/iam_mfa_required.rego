# IAM-003: MFA Required for Privileged Users
# Maps to: Vodafone CYBER_038 D1-D5 (Management of privileged access rights)
package grc.iam.mfa_required

default allow = false

allow {
    input.MFAEnabled == true
}

finding = msg {
    not allow
    msg = sprintf("Privileged IAM user %s does not have MFA enabled", [input.UserName])
}

finding = msg {
    allow
    msg = sprintf("Privileged IAM user %s has MFA enabled", [input.UserName])
}
