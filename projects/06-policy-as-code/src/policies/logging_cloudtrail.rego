# LOG-001: CloudTrail Must Be Enabled in All Regions
# Maps to: Vodafone CYBER_038 D1-D7 (Security event logging and monitoring)
package grc.logging.cloudtrail

default allow = false

allow {
    input.IsMultiRegionTrail == true
    input.IncludeGlobalServiceEvents == true
}

finding = msg {
    input.IsMultiRegionTrail == false
    msg = sprintf("CloudTrail trail %s is not a multi-region trail", [input.TrailName])
}

finding = msg {
    input.IncludeGlobalServiceEvents == false
    msg = sprintf("CloudTrail trail %s does not include global service events", [input.TrailName])
}

finding = msg {
    allow
    msg = sprintf("CloudTrail trail %s is multi-region with global service events enabled", [input.TrailName])
}
