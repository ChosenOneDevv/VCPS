# Project artifact contract

Artifact layout and record schema version: `0.1.0`; project configuration
schema version: `0.2.0`; VCPS specification: `1.0.0`. The project schema
adds portable Setup Engine progress and mutation-plan state. See
[contract.md](contract.md#unknown-fields-and-migrations) for migration.

- [contract.md](contract.md) defines layout, canonical ownership, IDs, and
  migration.
- [validation.md](validation.md) defines structural and cross-record checks.
- [schemas/](schemas/) contains JSON Schema 2020-12 definitions for YAML
  documents and Markdown YAML frontmatter.
- [examples/](examples/) contains minimal installation templates. Mint new
  IDs and replace example observations before use.

This layer defines records; it does not execute setup or validation.
