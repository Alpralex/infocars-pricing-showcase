select state, state_name, region, sort_order
from {{ ref('states') }}
