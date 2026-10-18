# Nightly encrypted backups to S3 and/or a synced folder

With the Sheet retired, one SQLite file holds all history. A nightly job snapshots it with the SQLite backup API, encrypts it client-side with age, and writes it to the targets enabled in settings: an S3 bucket with lifecycle retention and/or a cloud-synced folder. AWS only ever stores ciphertext.
