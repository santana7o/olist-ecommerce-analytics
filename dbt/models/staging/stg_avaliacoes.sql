select
    review_id                                  as avaliacao_id,
    order_id                                   as pedido_id,
    review_score                               as nota,
    review_creation_date                       as avaliado_em,
    tem_comentario
from {{ source('silver', 'order_reviews') }}
