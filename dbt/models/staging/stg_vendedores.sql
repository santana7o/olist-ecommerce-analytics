select
    seller_id                                  as vendedor_id,
    seller_zip_code_prefix                     as cep_prefixo,
    seller_city                                as cidade,
    seller_state                               as uf
from {{ source('silver', 'sellers') }}
