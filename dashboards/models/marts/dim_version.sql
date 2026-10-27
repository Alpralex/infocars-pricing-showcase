-- Canonical versions from infocars/catalog.py (23 versions of 7 models).
select
    version_key,
    make, model, version,
    make_name,
    model_name,
    version_name,
    model_name || ' ' || version_name   as car_name,
    body_type,
    sort_order
from {{ ref('catalog_versions') }}
