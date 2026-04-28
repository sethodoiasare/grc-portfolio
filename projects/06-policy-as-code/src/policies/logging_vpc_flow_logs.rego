# LOG-003: VPC Flow Logs Enabled
# Maps to: Vodafone CYBER_038 D1-D7 (Security event logging and monitoring)
package grc.logging.vpc_flow_logs

default allow = false

allow {
    input.FlowLogsEnabled == true
}

finding = msg {
    not allow
    msg = sprintf("VPC %s does not have flow logs enabled", [input.VpcId])
}

finding = msg {
    allow
    msg = sprintf("VPC %s has flow logs publishing to %s", [input.VpcId, input.FlowLogsDestination])
}
