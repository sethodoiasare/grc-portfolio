# ENC-003: RDS Instances Must Be Encrypted
# Maps to: Vodafone CYBER_038 D1-D17 (Protection of information in transit and at rest)
package grc.encryption.rds

default allow = false

allow {
    input.StorageEncrypted == true
}

finding = msg {
    not allow
    msg = sprintf("RDS instance %s does not have storage encryption enabled", [input.DBInstanceIdentifier])
}

finding = msg {
    allow
    msg = sprintf("RDS instance %s has storage encryption enabled with KMS key %s",
                  [input.DBInstanceIdentifier, input.KmsKeyId])
}
