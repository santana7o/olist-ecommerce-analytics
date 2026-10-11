with dias as (
    select cast(d as date) as data
    from range(date '2016-09-01', date '2018-11-01', interval 1 day) t(d)
)
select
    data,
    year(data)                                   as ano,
    quarter(data)                                as trimestre,
    month(data)                                  as mes,
    ['Jan','Fev','Mar','Abr','Mai','Jun','Jul','Ago','Set','Out','Nov','Dez'][month(data)] as nome_mes,
    day(data)                                    as dia,
    isodow(data)                                 as dia_semana_num,
    ['Seg','Ter','Qua','Qui','Sex','Sáb','Dom'][isodow(data)] as dia_semana,
    isodow(data) >= 6                            as fim_de_semana,
    date_trunc('month', data)                    as inicio_mes
from dias
