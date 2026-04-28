# IAM-001: IAM Least Privilege — No Wildcard Actions
# Maps to: Vodafone CYBER_038 D1-D5 (Management of privileged access rights)
package grc.iam.least_privilege

default allow = false

# Deny if Action contains wildcard
deny_wildcard_action {
    input.Action[_] == "*"
}

# Deny if Resource contains wildcard
deny_wildcard_resource {
    input.Resource[_] == "*"
}

allow {
    not deny_wildcard_action
    not deny_wildcard_resource
}

# Finding message
finding = msg {
    deny_wildcard_action
    msg = sprintf("IAM policy %s contains wildcard '*' in Action element", [input.PolicyName])
}

finding = msg {
    deny_wildcard_resource
    msg = sprintf("IAM policy %s contains wildcard '*' in Resource element", [input.PolicyName])
}

finding = msg {
    allow
    msg = sprintf("IAM policy %s uses scoped actions and resources", [input.PolicyName])
}
