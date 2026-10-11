-- Fato no grão de pedido.
select
    pedido_id,
    cliente_id,
    data_compra,
    status,
    pedido_valido,
    qtd_itens,
    valor_produtos,
    valor_frete,
    valor_total,
    valor_pago,
    forma_pagamento_principal,
    parcelas,
    categoria_principal,
    nota,
    foi_entregue,
    dias_para_entrega,
    dias_de_atraso,
    entregue_no_prazo
from {{ ref('int_pedidos_enriquecidos') }}
