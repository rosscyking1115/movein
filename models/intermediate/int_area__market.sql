-- Latest-year Land Registry sale context per MSOA: matched transaction count and
-- median sale price. rpt_area_profile_mvp derives the sample-depth confidence
-- flag and "why this area" text from these.
select
    dpg.area_id,
    count(fct.transaction_id) filter (
        where fct.transferred_year = {{ var('landreg_end_year') }}
    ) as sales_count_latest_year,
    cast(
        median(fct.price_gbp) filter (
            where fct.transferred_year = {{ var('landreg_end_year') }}
        ) as bigint
    ) as median_sale_price_gbp
from {{ ref('dim_postcode_geography') }} as dpg
left join {{ ref('fct_transactions') }} as fct
    on dpg.postcode = upper(trim(fct.postcode))
group by dpg.area_id
