# ENC-002: EBS Volumes Must Be Encrypted
# Maps to: Vodafone CYBER_038 D1-D17 (Protection of information in transit and at rest)
package grc.encryption.ebs

default allow = false

allow {
    input.Encrypted == true
}

finding = msg {
    not allow
    msg = sprintf("EBS volume %s in %s is not encrypted", [input.VolumeId, input.AvailabilityZone])
}

finding = msg {
    allow
    msg = sprintf("EBS volume %s in %s is encrypted with KMS key %s",
                  [input.VolumeId, input.AvailabilityZone, input.KmsKeyId])
}
