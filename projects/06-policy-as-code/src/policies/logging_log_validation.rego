# LOG-002: CloudTrail Log File Validation
# Maps to: Vodafone CYBER_038 D1-D7 (Security event logging and monitoring)
package grc.logging.log_validation

default allow = false

allow {
    input.LogFileValidationEnabled == true
}

finding = msg {
    not allow
    msg = sprintf("CloudTrail trail %s does not have log file validation enabled", [input.TrailName])
}

finding = msg {
    allow
    msg = sprintf("CloudTrail trail %s has log file validation enabled", [input.TrailName])
}
