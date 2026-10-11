-- Uma linha por pedido, juntando itens, pagamentos, avaliação e métricas de entrega.
with itens as (
    select
        i.pedido_id,
        count(*)                        as qtd_itens,
        count(distinct i.vendedor_id)   as qtd_vendedores,
        sum(i.preco)                    as valor_produtos,
        sum(i.frete)                    as valor_frete,
        sum(i.preco + i.frete)          as valor_total,
        -- categoria do item mais caro = categoria principal do pedido
        arg_max(p.categoria, i.preco)   as categoria_principal
    from {{ ref('stg_itens_pedido') }} i
    left join {{ ref('stg_produtos') }} p using (produto_id)
    group by 1
),

pagamentos as (
    select
        pedido_id,
        sum(valor_pago)                    as valor_pago,
        arg_max(forma_pagamento, valor_pago) as forma_pagamento_principal,
        max(parcelas)                      as parcelas
    from {{ ref('stg_pagamentos') }}
    group by 1
)

select
    o.pedido_id,
    o.cliente_id,
    o.status,
    o.comprado_em,
    o.data_compra,
    o.entregue_em,
    o.data_prevista_entrega,
    it.qtd_itens,
    it.qtd_vendedores,
    it.valor_produtos,
    it.valor_frete,
    it.valor_total,
    it.categoria_principal,
    pg.valor_pago,
    pg.forma_pagamento_principal,
    pg.parcelas,
    av.nota,
    o.status not in ('canceled', 'unavailable')                         as pedido_valido,
    o.entregue_em is not null                                           as foi_entregue,
    date_diff('day', o.comprado_em, o.entregue_em)                      as dias_para_entrega,
    date_diff('day', o.data_prevista_entrega, cast(o.entregue_em as date)) as dias_de_atraso,
    case when o.entregue_em is null then null
         else cast(o.entregue_em as date) <= o.data_prevista_entrega end as entregue_no_prazo
from {{ ref('stg_pedidos') }} o
left join itens      it using (pedido_id)
left join pagamentos pg using (pedido_id)
left join {{ ref('stg_avaliacoes') }} av using (pedido_id)
