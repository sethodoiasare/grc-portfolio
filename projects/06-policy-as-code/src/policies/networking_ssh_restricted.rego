# NET-001: No Unrestricted SSH (0.0.0.0/0)
# Maps to: Vodafone CYBER_038 D1-D10 (Network security and segregation)
package grc.networking.ssh_restricted

default allow = false

deny_unrestricted_ssh {
    rule = input.SecurityGroupRules[_]
    rule.Protocol == "tcp"
    rule.FromPort == 22
    rule.ToPort == 22
    rule.CidrIp == "0.0.0.0/0"
}

allow {
    not deny_unrestricted_ssh
}

finding = msg {
    deny_unrestricted_ssh
    msg = sprintf("Security group %s allows inbound SSH (port 22) from 0.0.0.0/0", [input.GroupId])
}

finding = msg {
    allow
    msg = sprintf("Security group %s restricts SSH to authorised IP ranges", [input.GroupId])
}
