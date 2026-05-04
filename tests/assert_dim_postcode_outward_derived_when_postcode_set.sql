-- Risk: postcode_outward is parsed from postcode in int_; if the parser
--       silently produced NULL or empty for a non-null postcode, downstream
--       outward-level aggregations would lose rows.
--
-- Fail rows: any postcode where outward couldn't be derived.

select
    postcode,
    postcode_outward
from {{ ref('dim_postcode') }}
where postcode is not null
  and (postcode_outward is null or postcode_outward = '')
