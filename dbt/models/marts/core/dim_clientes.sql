select
    c.cliente_id,
    c.cliente_unico_id,
    c.cidade,
    c.uf,
    r.estado,
    r.regiao
from {{ ref('stg_clientes') }} c
left join {{ ref('uf_regioes') }} r on c.uf = r.uf
