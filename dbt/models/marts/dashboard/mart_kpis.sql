-- Indicadores do dashboard calculados em SQL (usados para conferir o Tableau).
select
    sum(receita)                                   as receita,
    count(*)                                       as pedidos,
    sum(receita) / count(*)                        as ticket_medio,
    count(distinct cliente_unico_id)               as clientes,
    avg(entregue_no_prazo)                         as pct_entregue_no_prazo,
    avg(nota)                                      as nota_media,
    avg(dias_para_entrega)                         as prazo_medio_entrega_dias,
    sum(valor_frete) / sum(receita)                as pct_frete_na_receita
from {{ ref('mart_pedidos_dashboard') }}
