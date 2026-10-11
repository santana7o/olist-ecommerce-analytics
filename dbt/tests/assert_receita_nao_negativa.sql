-- O teste falha se retornar alguma linha.
select pedido_id, receita
from {{ ref('mart_pedidos_dashboard') }}
where receita < 0
