# AGPL-3.0, one user per install, personal data outside git

Licensed under the GNU Affero General Public License v3.0 so that a hosted fork must publish its source. Each install serves one person on localhost, with no login. Everything personal (config/, data/, knowledge/, .env) is git-ignored; the repo ships config.example/ with a fake persona. Course material used for RAG is never committed, for copyright reasons.

## Considered Options

- MIT: simpler, but allows a closed SaaS built on the project.
- Multi-user with auth: large scope increase with no need for it.
