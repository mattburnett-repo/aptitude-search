-- occupation_embeddings: one row per O*NET occupation for aptitude-to-jobtype matching.
-- Embedding model: BAAI/bge-large-en-v1.5 (1024 dimensions, cosine similarity).
-- Safe to re-run: ensures extension, table, and index; clears all rows.

CREATE TABLE IF NOT EXISTS occupation_embeddings (
  onetsoc_code       character(10) PRIMARY KEY
                     REFERENCES occupation_data (onetsoc_code),
  occupation_profile text NOT NULL,
  embedding          vector(1024) NOT NULL,
  created_at         timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS occupation_embeddings_embedding_hnsw_idx
  ON occupation_embeddings
  USING hnsw (embedding vector_cosine_ops);

TRUNCATE occupation_embeddings;
