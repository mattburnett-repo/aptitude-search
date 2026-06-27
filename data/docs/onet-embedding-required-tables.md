# Embedding-required tables (`occupation_profile_from_onet.sql`)

Tables required to build occupation profile text for `data/embed/build_occupation_embeddings.py`.  
`scales_reference` is not queried by the embedding SQL but is required for FK constraints when loading `abilities` and skills tables.

| Table                     | File                             | INSERT count |
| ------------------------- | -------------------------------- | -----------: |
| `content_model_reference` | `01_content_model_reference.sql` |        3,006 |
| `scales_reference`        | `04_scales_reference.sql`        |           32 |
| `occupation_data`         | `03_occupation_data.sql`         |        1,016 |
| `abilities`               | `12_abilities.sql`               |       92,976 |
| `essential_skills`        | `24_essential_skills.sql`        |       17,880 |
| `transferable_skills`     | `25_transferable_skills.sql`     |       44,700 |
| `job_titles`              | `36_job_titles.sql`              |       57,543 |

**Total: 217,153 INSERT statements across 7 files** (~18% of all INSERTs).

Load only these files locally: `ONET_EMBED_ONLY=1 ./data/load-onet-postgres.sh` (see [../README.md](../README.md)).

See [db_30_3_mysql-insert-counts.md](db_30_3_mysql-insert-counts.md) for full O*NET INSERT counts.
