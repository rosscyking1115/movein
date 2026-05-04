-- Risk: a premium% above 250% or below -50% almost always indicates a
--       region+year with too few new-build sales for the median to be
--       stable, or an upstream is_new_build_flag mis-mapping.
--       (We saw +61% in the North East for 2025 — that's high but
--        defensible given new-build scarcity. >250% is not.)
--
-- Fail rows: any (region, year) where premium_pct is outside [-50, +250].

select
    region,
    transferred_year,
    new_build_count,
    existing_count,
    premium_pct
from {{ ref('rpt_new_build_premium') }}
where premium_pct is not null
  and (premium_pct < -50 or premium_pct > 250)
