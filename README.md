# Olist E-commerce Analytics: atraso na entrega x satisfação do cliente

Projeto de análise de dados ponta a ponta com o dataset público do marketplace Olist: cerca de 96 mil pedidos entregues entre jan/2017 e ago/2018, do dado bruto ao dashboard.

**Pergunta de negócio:** atrasos na entrega derrubam a satisfação do cliente? Onde isso é mais grave e quanta receita está envolvida?

**Dashboard interativo no Tableau Public:** [abrir o dashboard](https://public.tableau.com/app/profile/felipe.gabriel.coelho.de.santana/viz/olist_dashboard_final/DashboardOlist)

---

## Principais resultados

| Achado | Número |
|---|---|
| Nota média do pedido entregue adiantado | **4,30** |
| Nota com 1 a 3 dias de atraso | **3,75** |
| Nota com 4 a 7 dias de atraso | **2,30** |
| Nota com 8 dias ou mais de atraso | **1,73** |
| Pedidos atrasados com nota 1 ou 2 | **54%** (contra 9% dos pontuais) |
| Taxa de atraso no Nordeste | **14,3%**, o dobro do Sul (7,0%) |
| Vendas que passaram por pedidos atrasados | **cerca de R$ 1,15 milhão** |

**Recomendações**

- Prazos prometidos mais realistas para o Nordeste e o RJ.
- Alerta operacional a partir de 4 dias de atraso, ponto em que a nota desaba.
- Investigar móveis de escritório, a categoria com a pior nota.

---

## Arquitetura

```
Kaggle (Brazilian E-Commerce Public Dataset by Olist, 9 CSVs)
        |
        v
Google Colab / Jupyter  -- notebooks/01_ingestao_limpeza.ipynb
  ingestão, perfil dos dados, limpeza, validações
        |
        v
DuckDB  data/olist.duckdb
  bronze  (CSVs como vieram da fonte)
  silver  (dados limpos e tipados)
        |
        v
dbt (dbt-duckdb)
  staging -> intermediate -> marts (core + dashboard)
  57 testes de qualidade (PASS=57, ERROR=0)
        |
        +--> DBeaver: sql/analises.sql (10 análises de negócio)
        |
        v
Tableau  tableau/olist_dashboard.twbx
```

Tudo é orquestrado por `pipeline.py`.

---

## Limpeza dos dados (Python / pandas)

- **Carga:** 9 tabelas, 99.441 pedidos e 1 milhão de linhas de geolocalização.
- **Recorte:** só meses completos (jan/2017 a ago/2018), 99.092 pedidos.
- **Deduplicação:** 547 pedidos tinham mais de uma avaliação; ficou a mais recente, e 1 forma de pagamento principal por pedido.
- **Geolocalização:** 42 coordenadas fora do Brasil removidas, resumo em 19.010 prefixos de CEP.
- **Categorias:** traduzidas e padronizadas; 610 produtos sem categoria viraram "Unknown".
- **Junção:** 112.279 linhas (1 por item) e 98.353 pedidos.
- **Métricas:** prazo, dias de atraso, flag e faixas de atraso.
- **Checagem:** 8,1% de atraso e nota 4,16 antes de ir para o Tableau.

## Modelagem

Só pedidos entregues. Como pedidos com vários itens repetem nota e prazo, as métricas são calculadas por pedido para não inflar as médias.

| Camada dbt | Modelos |
|---|---|
| staging | `stg_pedidos`, `stg_itens_pedido`, `stg_pagamentos`, `stg_avaliacoes`, `stg_clientes`, `stg_produtos`, `stg_vendedores` |
| intermediate | `int_pedidos_enriquecidos` |
| marts/core | `fct_pedidos`, `fct_itens_pedido`, `dim_clientes`, `dim_produtos`, `dim_vendedores`, `dim_calendario` |
| marts/dashboard | `mart_pedidos_dashboard`, `mart_kpis` |

Testes: unicidade, não nulos, integridade referencial e testes de negócio (`assert_receita_nao_negativa`, `assert_pagamento_confere_com_itens`).

## Dashboard

KPIs, mapa por estado (o clique filtra o painel), nota por faixa de atraso, evolução mensal e ranking de categorias.

---

## Como rodar

```bash
python3 pipeline.py            # roda tudo
python3 pipeline.py dbt        # só uma etapa: setup | notebook | dbt | export | kpis
```

O pipeline cria o ambiente virtual, baixa os dados, executa o notebook, roda `dbt build`, exporta a camada gold para o Tableau e mostra os KPIs finais. No Mac, `rodar_pipeline.command` roda tudo com dois cliques.

## Estrutura

```
notebooks/   ingestão e limpeza (bronze e silver)
dbt/         modelos staging, intermediate e marts, testes e seeds
sql/         10 análises de negócio em SQL (window functions, CTEs)
scripts/     exportação para o Tableau e geração do workbook
tableau/     workbooks .twbx e imagens de fundo
pipeline.py  orquestração de ponta a ponta
```

## Tecnologias

Python (pandas), DuckDB, dbt, SQL, Tableau, Google Colab.

---

Felipe Gabriel Coelho de Santana, Analista de Dados. [LinkedIn](https://www.linkedin.com/in/felipe-gabriel-coelho-de-santana-a33b49304)
