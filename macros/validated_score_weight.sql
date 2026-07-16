{% macro validated_score_weight(component) %}
    {% set key = 'score_weight_' ~ component %}
    {% set raw_weight = var(key) %}
    {% set minimum = var('score_weight_min') | float %}
    {% set maximum = var('score_weight_max') | float %}

    {% if raw_weight is not number %}
        {{ exceptions.raise_compiler_error(key ~ ' must be a numeric scoring weight.') }}
    {% endif %}

    {% set weight = raw_weight | float %}
    {% if weight != weight or weight < minimum or weight > maximum %}
        {{ exceptions.raise_compiler_error(
            key ~ ' must be between ' ~ minimum ~ ' and ' ~ maximum ~
            ' under scoring contract v2.'
        ) }}
    {% endif %}

    {{ return(weight) }}
{% endmacro %}
