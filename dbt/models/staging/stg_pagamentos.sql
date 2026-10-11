select
    order_id                                   as pedido_id,
    payment_sequential                         as sequencia_pagamento,
    case payment_type
        when 'credit_card' then 'Cartão de crédito'
        when 'debit_card'  then 'Cartão de débito'
        when 'boleto'      then 'Boleto'
        when 'voucher'     then 'Voucher'
        else 'Não definido'
    end                                        as forma_pagamento,
    payment_installments                       as parcelas,
    cast(payment_value as decimal(12, 2))      as valor_pago
from {{ source('silver', 'order_payments') }}
