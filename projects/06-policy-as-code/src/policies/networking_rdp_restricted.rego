# NET-002: No Unrestricted RDP (0.0.0.0/0)
# Maps to: Vodafone CYBER_038 D1-D10 (Network security and segregation)
package grc.networking.rdp_restricted

default allow = false

deny_unrestricted_rdp {
    rule = input.SecurityGroupRules[_]
    rule.Protocol == "tcp"
    rule.FromPort == 3389
    rule.ToPort == 3389
    rule.CidrIp == "0.0.0.0/0"
}

allow {
    not deny_unrestricted_rdp
}

finding = msg {
    deny_unrestricted_rdp
    msg = sprintf("Security group %s allows inbound RDP (port 3389) from 0.0.0.0/0", [input.GroupId])
}

finding = msg {
    allow
    msg = sprintf("Security group %s restricts RDP to authorised IP ranges", [input.GroupId])
}
