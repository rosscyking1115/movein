-- Risk: an area median computed from a handful of transactions is an outlier
--       magnet (prime-central areas can show a £13M median from 2 sales). The
--       profile must never present such a median as reliable market context.
--
-- Fail rows: any area whose latest-year sales are below the reliability
-- threshold but whose median is still flagged 'reliable', or any area with a
-- non-null median that is left unflagged ('none').

select
    area_id,
    sales_count_latest_year,
    median_sale_price_confidence
from {{ ref('rpt_area_profile_mvp') }}
where
    (
        sales_count_latest_year < {{ var('min_reliable_sale_sample') }}
        and median_sale_price_confidence = 'reliable'
    )
    or (
        median_sale_price_gbp is not null
        and median_sale_price_confidence = 'none'
    )
