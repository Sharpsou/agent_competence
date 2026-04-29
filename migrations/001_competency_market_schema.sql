create extension if not exists pgcrypto;

create table if not exists companies (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  normalized_name text not null,
  created_at timestamptz not null default now(),
  unique (normalized_name)
);

create table if not exists job_search_runs (
  id uuid primary key default gen_random_uuid(),
  request_keyword text not null,
  request_job_title text,
  request_payload jsonb not null,
  created_at timestamptz not null default now()
);

create table if not exists job_offers (
  id uuid primary key default gen_random_uuid(),
  source text not null,
  source_job_id text not null,
  company_id uuid references companies(id) on delete set null,
  title text not null,
  normalized_title text not null,
  location_text text not null,
  remote_mode text not null,
  contract_type text not null,
  description_text text not null,
  published_at text not null,
  detail_url text,
  raw_payload jsonb,
  created_at timestamptz not null default now(),
  unique (source, source_job_id)
);

create table if not exists job_search_run_offers (
  run_id uuid not null references job_search_runs(id) on delete cascade,
  offer_id uuid not null references job_offers(id) on delete cascade,
  primary key (run_id, offer_id)
);

create table if not exists competencies (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  normalized_name text not null,
  category text not null,
  created_at timestamptz not null default now(),
  unique (normalized_name)
);

create table if not exists competency_observations (
  id uuid primary key default gen_random_uuid(),
  run_id uuid not null references job_search_runs(id) on delete cascade,
  offer_id uuid not null references job_offers(id) on delete cascade,
  company_id uuid references companies(id) on delete set null,
  competency_id uuid not null references competencies(id) on delete cascade,
  confidence numeric(4, 3) not null check (confidence >= 0 and confidence <= 1),
  matched_text text not null,
  extractor_name text not null,
  verifier_status text not null,
  created_at timestamptz not null default now()
);

create index if not exists job_offers_company_id_idx on job_offers (company_id);
create index if not exists job_offers_title_idx on job_offers (normalized_title);
create index if not exists job_search_run_offers_offer_id_idx on job_search_run_offers (offer_id);
create index if not exists competency_observations_run_id_idx on competency_observations (run_id);
create index if not exists competency_observations_offer_id_idx on competency_observations (offer_id);
create index if not exists competency_observations_company_id_idx on competency_observations (company_id);
create index if not exists competency_observations_competency_id_idx
  on competency_observations (competency_id);
create index if not exists competency_observations_competency_run_idx
  on competency_observations (competency_id, run_id);
