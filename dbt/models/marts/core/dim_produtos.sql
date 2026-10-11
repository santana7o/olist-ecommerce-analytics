select produto_id, categoria, categoria_en, qtd_fotos, peso_g, volume_cm3
from {{ ref('stg_produtos') }}
