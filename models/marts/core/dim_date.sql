{{
    config(
        materialized='table'
    )
}}

-- dim_date — generated calendar covering the configured analysis window
-- plus one buffer year on either side so date-spine joins on transferred_on
-- never find a missing key. Update landreg_start_year/landreg_end_year in
-- dbt_project.yml when extending the project to a new complete Land Registry
-- year; the spine expands automatically.
--
-- Per kit lesson L6 we lean on dbt_date.get_date_dimension rather than
-- hand-rolling DATE arithmetic. The macro itself produces a complete
-- SELECT — no `select * from` wrapper. It returns ~30 calendar columns
-- (date_day, day_of_week, month, quarter, ISO week, fiscal year, etc.).

{% set date_spine_start = (var('landreg_start_year') - 1) ~ '-01-01' %}
{% set date_spine_exclusive_end = (var('landreg_end_year') + 2) ~ '-01-01' %}

{{ dbt_date.get_date_dimension(date_spine_start, date_spine_exclusive_end) }}
