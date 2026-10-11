-- Tabela "larga" (one big table) que alimenta o Tableau.
-- Período com meses completos: jan/2017 a ago/2018. Só pedidos válidos (sem cancelados/indisponíveis).
select
    f.pedido_id,
    f.data_compra,
    cal.ano,
    cal.mes,
    cal.nome_mes,
    cal.dia_semana,
    c.uf,
    c.estado,
    c.regiao,
    c.cliente_unico_id,
    f.categoria_principal,
    f.forma_pagamento_principal,
    f.qtd_itens,
    f.valor_produtos,
    f.valor_frete,
    f.valor_total                    as receita,
    f.nota,
    f.dias_para_entrega,
    f.dias_de_atraso,
    case when f.entregue_no_prazo then 1 when f.entregue_no_prazo = false then 0 end as entregue_no_prazo
from {{ ref('fct_pedidos') }} f
join {{ ref('dim_clientes') }}  c   using (cliente_id)
join {{ ref('dim_calendario') }} cal on f.data_compra = cal.data
where f.pedido_valido
  and f.valor_total is not null
  and f.data_compra between date '2017-01-01' and date '2018-08-31'
