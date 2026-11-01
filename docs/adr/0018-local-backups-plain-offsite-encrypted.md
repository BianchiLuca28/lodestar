# Local backups are plain copies; only off-site copies are encrypted

Supersedes the encryption scope of ADR 0011.

ADR 0011 encrypted every backup with `age`. For a backup that stays on the same PC as the database, encryption protects nothing the database itself does not already expose, and it adds a key the user can lose, which would make every backup unreadable. The user also runs the PC about once a week, so a fixed nightly time would rarely fire.

So the folder target keeps plain SQLite copies under the data dir (`data/backups/` by default), made at startup and hourly whenever the newest backup is over a day old, with retention counted in days and months that have a backup (30 and 12). Copies that leave the machine (the S3 target, v0.2) are still encrypted client-side with `age`, so AWS only ever sees ciphertext.

**Considered:** encrypting the local folder too (rejected: no gain on the same disk, key-loss risk); a cron-style nightly time (rejected: the PC is often off at that hour).
