{{
    config(
        materialized='table'
    )
}}

-- dim_date — generated 7-year calendar covering one year either side of the
-- 2021-2025 transaction range so date-spine joins on transferred_on never
-- find a missing key.
--
-- Per kit lesson L6 we lean on dbt_date.get_date_dimension rather than
-- hand-rolling DATE arithmetic. The macro itself produces a complete
-- SELECT — no `select * from` wrapper. It returns ~30 calendar columns
-- (date_day, day_of_week, month, quarter, ISO week, fiscal year, etc.).

{{ dbt_date.get_date_dimension('2020-01-01', '2026-12-31') }}
