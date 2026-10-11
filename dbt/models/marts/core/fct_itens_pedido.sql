-- Fato no grão de item de pedido.
select
    i.item_pedido_id,
    i.pedido_id,
    o.cliente_id,
    i.produto_id,
    i.vendedor_id,
    o.data_compra,
    i.preco,
    i.frete,
    i.preco + i.frete as valor_total
from {{ ref('stg_itens_pedido') }} i
join {{ ref('stg_pedidos') }} o using (pedido_id)
