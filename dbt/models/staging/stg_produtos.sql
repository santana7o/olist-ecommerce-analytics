select
    p.product_id                                           as produto_id,
    p.product_category_name                                as categoria_original,
    -- "cama_mesa_banho" -> "Cama mesa banho"
    upper(left(replace(p.product_category_name, '_', ' '), 1))
        || substr(replace(p.product_category_name, '_', ' '), 2) as categoria,
    coalesce(t.product_category_name_english, 'no_category') as categoria_en,
    p.product_photos_qty                                   as qtd_fotos,
    p.product_weight_g                                     as peso_g,
    p.product_length_cm * p.product_height_cm * p.product_width_cm as volume_cm3
from {{ source('silver', 'products') }} p
left join {{ source('silver', 'category_translation') }} t
    on p.product_category_name = t.product_category_name
