# IAM-002: No Attached Admin Policies
# Maps to: Vodafone CYBER_038 D1-D5 (Management of privileged access rights)
package grc.iam.no_admin_policies

default allow = false

admin_policies = {"AdministratorAccess", "PowerUserAccess", "IAMFullAccess"}

deny_admin_attached {
    input.AttachedPolicies[_].PolicyName == admin_policies[_]
}

allow {
    not deny_admin_attached
}

finding = msg {
    deny_admin_attached
    msg = sprintf("IAM principal %s has admin-level policy %s attached directly",
                  [input.PrincipalName, input.AttachedPolicies[_].PolicyName])
}

finding = msg {
    allow
    msg = sprintf("IAM principal %s has no directly attached admin policies", [input.PrincipalName])
}
