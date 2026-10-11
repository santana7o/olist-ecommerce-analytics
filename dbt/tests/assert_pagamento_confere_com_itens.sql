-- Em pedidos entregues, o valor pago deve bater com itens + frete (tolerância de R$ 1).
-- Aceitamos até 1% de divergência (juros de parcelamento e vouchers).
with divergentes as (
    select count(*) as qtd
    from {{ ref('fct_pedidos') }}
    where status = 'delivered'
      and abs(valor_pago - valor_total) > 1
),
total as (select count(*) as qtd from {{ ref('fct_pedidos') }} where status = 'delivered')
select d.qtd, t.qtd
from divergentes d, total t
where d.qtd > 0.01 * t.qtd
