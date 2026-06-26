-- Build occupation_profile text from O*NET (title, description, abilities, skills, job titles).
-- Used by data/ingest/build_occupation_embeddings.py

SELECT
  od.onetsoc_code,
  concat_ws(
    E'\n',
    'Title: ' || od.title,
    'Description: ' || od.description,
    'Abilities: ' || COALESCE(ab.names, ''),
    'Skills: ' || COALESCE(sk.names, ''),
    'Titles: ' || COALESCE(jt.names, '')
  ) AS occupation_profile
FROM occupation_data od
LEFT JOIN LATERAL (
  SELECT string_agg(element_name, ', ' ORDER BY data_value DESC) AS names
  FROM (
    SELECT cmr.element_name, a.data_value
    FROM abilities a
    JOIN content_model_reference cmr ON cmr.element_id = a.element_id
    WHERE a.onetsoc_code = od.onetsoc_code
      AND a.scale_id = 'IM'
    ORDER BY a.data_value DESC
    LIMIT 10
  ) ability_rows
) ab ON true
LEFT JOIN LATERAL (
  SELECT string_agg(element_name, ', ' ORDER BY data_value DESC) AS names
  FROM (
    SELECT cmr.element_name, s.data_value
    FROM (
      SELECT onetsoc_code, element_id, scale_id, data_value
      FROM essential_skills
      UNION ALL
      SELECT onetsoc_code, element_id, scale_id, data_value
      FROM transferable_skills
    ) s
    JOIN content_model_reference cmr ON cmr.element_id = s.element_id
    WHERE s.onetsoc_code = od.onetsoc_code
      AND s.scale_id = 'IM'
    ORDER BY s.data_value DESC
    LIMIT 10
  ) skill_rows
) sk ON true
LEFT JOIN LATERAL (
  SELECT string_agg(job_title, ', ') AS names
  FROM (
    SELECT job_title
    FROM job_titles
    WHERE onetsoc_code = od.onetsoc_code
    ORDER BY job_title
    LIMIT 10
  ) title_rows
) jt ON true
ORDER BY od.onetsoc_code;
