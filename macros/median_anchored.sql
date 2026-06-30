{#
  Median-anchored winsorised min-max for a higher-is-better value → 0-100.
  Clips to [lo, hi] (the 2nd/98th percentiles), then maps lo→0, md(median)→50,
  hi→100. This puts the typical area at 50 and preserves magnitude, unlike a pure
  percentile rank. For lower-is-better indicators, the caller uses 100 - this.
  Kept in sync with scripts/rescore_extract.py.
#}
{% macro median_anchored(col, lo, md, hi) %}
    case
        when {{ col }} is null then null
        when least(greatest({{ col }}, {{ lo }}), {{ hi }}) <= {{ md }}
            then 50.0 * (least(greatest({{ col }}, {{ lo }}), {{ hi }}) - {{ lo }})
                / nullif({{ md }} - {{ lo }}, 0)
        else 50.0 + 50.0 * (least(greatest({{ col }}, {{ lo }}), {{ hi }}) - {{ md }})
            / nullif({{ hi }} - {{ md }}, 0)
    end
{% endmacro %}
