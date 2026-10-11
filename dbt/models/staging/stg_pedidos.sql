select
    order_id                                   as pedido_id,
    customer_id                                as cliente_id,
    order_status                               as status,
    order_purchase_timestamp                   as comprado_em,
    cast(order_purchase_timestamp as date)     as data_compra,
    order_approved_at                          as aprovado_em,
    order_delivered_carrier_date               as enviado_em,
    order_delivered_customer_date              as entregue_em,
    cast(order_estimated_delivery_date as date) as data_prevista_entrega,
    flag_entrega_inconsistente
from {{ source('silver', 'orders') }}
