-- The first sentence of every evidence note must name the level it explains.

select
    area_id,
    evidence_quality_level,
    evidence_quality_notes
from {{ ref('rpt_neighbourhood_score') }}
where lower(evidence_quality_notes) not like evidence_quality_level || ' evidence:%'
