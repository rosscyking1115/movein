-- Risk: a malformed CSV row or a parsing bug could create a transferred_on
--       in the future; that pollutes YoY calculations and indicates a real
--       pipeline problem.
--
-- Fail rows: any fct row where the sale date is later than today.

select
    transaction_id,
    transferred_on
from {{ ref('fct_transactions') }}
where transferred_on > current_date
