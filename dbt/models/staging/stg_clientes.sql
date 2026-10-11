select
    customer_id                                as cliente_id,
    customer_unique_id                         as cliente_unico_id,
    customer_zip_code_prefix                   as cep_prefixo,
    customer_city                              as cidade,
    customer_state                             as uf
from {{ source('silver', 'customers') }}
