# O\*NET 30.3 SQL download

The MySQL-format SQL dumps are **not stored in git** (~300 MB, ~1.2M INSERTs). Download them locally before running `./data/load-onet-postgres.sh`.

## Download

1. Go to the [O\*NET 30.3 MySQL dictionary](https://www.onetcenter.org/dictionary/30.3/mysql/).
2. Download the database release (zip).
3. Extract so numbered SQL files land here:

```
data/download/db_30_3_mysql/
  01_content_model_reference.sql
  02_job_zone_reference.sql
  …
  45_work_styles_to_work_context.sql
```

4. Verify: `ls data/download/db_30_3_mysql/[0-9]*.sql | wc -l` should print `45`.

## License

O\*NET® content is © U.S. Department of Labor, Employment and Training Administration, licensed under [CC BY 4.0](https://www.onetcenter.org/license_db.html). See root [README.md](../../README.md#third-party-data).
