# IAM-004: Access Key Rotation (90 days)
# Maps to: Vodafone CYBER_038 D1-D5 (Management of privileged access rights)
package grc.iam.key_rotation

default allow = false

max_age_days = 90

deny_key_age {
    input.KeyAgeDays > max_age_days
}

allow {
    not deny_key_age
}

finding = msg {
    deny_key_age
    msg = sprintf("Access key %s for user %s is %d days old (exceeds 90-day limit)",
                  [input.AccessKeyId, input.UserName, input.KeyAgeDays])
}

finding = msg {
    allow
    msg = sprintf("Access key %s for user %s is within rotation window (%d days old)",
                  [input.AccessKeyId, input.UserName, input.KeyAgeDays])
}
