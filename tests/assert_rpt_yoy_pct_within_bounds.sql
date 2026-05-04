-- Risk: a |YoY|% above 50% almost always means an upstream issue (incomplete
--       year load, bad data, division-by-zero edge case). A real housing-market
--       move of that magnitude in a region across a single year would itself be
--       a story, but should be flagged for human review either way.
--
-- Fail rows: any (region, year) where |YoY%| exceeds 50.

select
    region,
    transferred_year,
    sales_count,
    median_yoy_pct,
    mean_yoy_pct
from {{ ref('rpt_price_yoy_by_region') }}
where (median_yoy_pct is not null and abs(median_yoy_pct) > 50)
   or (mean_yoy_pct   is not null and abs(mean_yoy_pct)   > 50)
