-- =====================================================================
-- Olist E-commerce Analytics — análises de negócio em SQL
-- Abra data/olist.duckdb no DBeaver (driver DuckDB) e rode cada bloco.
-- Todas as consultas usam a camada gold criada pelo dbt.
-- =====================================================================


-- 1) Visão geral do período (jan/2017 a ago/2018)
select
    round(sum(receita), 2)                      as receita,
    count(*)                                    as pedidos,
    round(sum(receita) / count(*), 2)           as ticket_medio,
    round(100 * avg(entregue_no_prazo), 1)      as pct_no_prazo,
    round(avg(nota), 2)                         as nota_media
from gold.mart_pedidos_dashboard;


-- 2) Crescimento mês a mês (window function LAG)
with mensal as (
    select date_trunc('month', data_compra) as mes, sum(receita) as receita
    from gold.mart_pedidos_dashboard
    group by 1
)
select
    strftime(mes, '%Y-%m')                                        as mes,
    round(receita, 2)                                             as receita,
    round(100 * (receita / lag(receita) over (order by mes) - 1), 1) as crescimento_mom_pct
from mensal
order by mes;


-- 3) Mesmo período, ano contra ano (jan–ago 2018 vs jan–ago 2017)
select
    ano,
    round(sum(receita), 2) as receita_jan_ago,
    count(*)               as pedidos
from gold.mart_pedidos_dashboard
where mes <= 8
group by ano
order by ano;


-- 4) Ranking de estados por receita + participação (RANK e SUM OVER)
select
    uf,
    regiao,
    round(sum(receita), 2)                                        as receita,
    rank() over (order by sum(receita) desc)                      as ranking,
    round(100 * sum(receita) / sum(sum(receita)) over (), 1)      as participacao_pct
from gold.mart_pedidos_dashboard
group by uf, regiao
order by ranking;


-- 5) Top 10 categorias por receita
select
    categoria_principal                  as categoria,
    count(*)                             as pedidos,
    round(sum(receita), 2)               as receita,
    round(avg(nota), 2)                  as nota_media
from gold.mart_pedidos_dashboard
group by 1
order by receita desc
limit 10;


-- 6) O atraso derruba a nota? (nota média por faixa de atraso)
select
    case
        when dias_de_atraso <= 0  then '1. No prazo'
        when dias_de_atraso <= 3  then '2. 1 a 3 dias de atraso'
        when dias_de_atraso <= 7  then '3. 4 a 7 dias de atraso'
        else                           '4. Mais de 7 dias de atraso'
    end                                  as faixa,
    count(*)                             as pedidos,
    round(avg(nota), 2)                  as nota_media,
    round(100 * avg(case when nota = 1 then 1 else 0 end), 1) as pct_nota_1
from gold.mart_pedidos_dashboard
where dias_de_atraso is not null and nota is not null
group by 1
order by 1;


-- 7) Prazo de entrega e atraso por região
select
    regiao,
    round(avg(dias_para_entrega), 1)         as prazo_medio_dias,
    round(100 * avg(entregue_no_prazo), 1)   as pct_no_prazo,
    round(100 * sum(valor_frete) / sum(receita), 1) as frete_sobre_receita_pct
from gold.mart_pedidos_dashboard
group by 1
order by prazo_medio_dias;


-- 8) Formas de pagamento
select
    forma_pagamento_principal            as forma_pagamento,
    count(*)                             as pedidos,
    round(100 * count(*) / sum(count(*)) over (), 1) as pct_pedidos,
    round(sum(receita) / count(*), 2)    as ticket_medio
from gold.mart_pedidos_dashboard
group by 1
order by pedidos desc;


-- 9) Recompra: quantos clientes compraram mais de uma vez?
with compras as (
    select cliente_unico_id, count(*) as pedidos
    from gold.mart_pedidos_dashboard
    group by 1
)
select
    count(*)                                              as clientes,
    count(*) filter (where pedidos > 1)                   as clientes_recorrentes,
    round(100 * count(*) filter (where pedidos > 1) / count(*), 1) as taxa_recompra_pct
from compras;


-- 10) Vendas por dia da semana
select
    dia_semana,
    count(*)                    as pedidos,
    round(sum(receita), 2)      as receita
from gold.mart_pedidos_dashboard
group by 1
order by pedidos desc;
