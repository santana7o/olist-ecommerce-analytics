select
    v.vendedor_id,
    v.cidade,
    v.uf,
    r.regiao
from {{ ref('stg_vendedores') }} v
left join {{ ref('uf_regioes') }} r on v.uf = r.uf
