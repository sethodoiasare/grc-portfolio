# ENC-001: S3 Buckets Must Use Server-Side Encryption
# Maps to: Vodafone CYBER_038 D1-D17 (Protection of information in transit and at rest)
package grc.encryption.s3_sse

default allow = false

allow {
    input.DefaultEncryption.Enabled == true
}

finding = msg {
    not allow
    msg = sprintf("S3 bucket %s does not have default server-side encryption enabled", [input.BucketName])
}

finding = msg {
    allow
    msg = sprintf("S3 bucket %s has default server-side encryption (%s) enabled",
                  [input.BucketName, input.DefaultEncryption.Algorithm])
}
