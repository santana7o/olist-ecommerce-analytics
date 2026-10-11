select
    order_id || '-' || order_item_id           as item_pedido_id,
    order_id                                   as pedido_id,
    order_item_id                              as sequencia_item,
    product_id                                 as produto_id,
    seller_id                                  as vendedor_id,
    shipping_limit_date                        as prazo_envio,
    cast(price as decimal(12, 2))              as preco,
    cast(freight_value as decimal(12, 2))      as frete
from {{ source('silver', 'order_items') }}
