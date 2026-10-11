"""Gera notebooks/01_ingestao_limpeza.ipynb (formato nbformat v4) a partir das células abaixo."""
import json
from pathlib import Path

cells = []


def md(txt):
    cells.append({"cell_type": "markdown", "metadata": {}, "source": txt.strip("\n").splitlines(True)})


def code(txt):
    cells.append({"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [],
                  "source": txt.strip("\n").splitlines(True)})


md("""
# 🛒 Olist E-commerce Analytics — 01. Ingestão e Limpeza

**Objetivo:** baixar os dados públicos do e-commerce Olist (~100 mil pedidos, 2016–2018), entender a qualidade dos dados, limpar e carregar tudo em um banco **DuckDB** para a modelagem com **dbt**.

Arquitetura em camadas (*medallion*):

| Camada | Onde | O que tem |
|---|---|---|
| 🥉 **bronze** | DuckDB (`bronze.*`) | CSVs exatamente como vieram da fonte |
| 🥈 **silver** | DuckDB (`silver.*`) | Dados limpos e tipados por este notebook |
| 🥇 **gold** | DuckDB (`gold.*`) | Fatos, dimensões e tabelas do dashboard, criados pelo **dbt** |

> Roda no **Google Colab** ou localmente (o notebook detecta o ambiente sozinho).
""")

code("""
# ---------- 1. Configuração do ambiente ----------
import sys, os, subprocess
from pathlib import Path

EM_COLAB = "google.colab" in sys.modules
if EM_COLAB:
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "duckdb", "kagglehub"], check=True)
    BASE = Path("/content/olist-ecommerce-analytics")
else:
    BASE = Path.cwd().parent if Path.cwd().name == "notebooks" else Path.cwd()

PASTA_RAW = BASE / "data" / "raw"
ARQUIVO_DB = BASE / "data" / "olist.duckdb"
PASTA_RAW.mkdir(parents=True, exist_ok=True)

import unicodedata
import numpy as np
import pandas as pd
import duckdb

pd.set_option("display.max_columns", 50)
print("Ambiente:", "Google Colab" if EM_COLAB else "local", "| pasta do projeto:", BASE)
""")

md("""
## 2. Extração
Fonte oficial: [Kaggle — Brazilian E-Commerce Public Dataset by Olist](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce).
Tenta baixar pelo `kagglehub`; se não der, usa um espelho público no GitHub. Se os arquivos já estiverem em `data/raw`, pula o download.
""")

code("""
# ---------- 2. Download dos dados ----------
import shutil, urllib.request

ARQUIVOS = {
    "orders": "olist_orders_dataset.csv",
    "order_items": "olist_order_items_dataset.csv",
    "order_payments": "olist_order_payments_dataset.csv",
    "order_reviews": "olist_order_reviews_dataset.csv",
    "customers": "olist_customers_dataset.csv",
    "sellers": "olist_sellers_dataset.csv",
    "products": "olist_products_dataset.csv",
    "category_translation": "product_category_name_translation.csv",
}
ESPELHO = "https://raw.githubusercontent.com/spdrio/Brazilian-E-Commerce-Public-Dataset-by-Olist/master/files/"

def baixar_dados():
    faltando = [f for f in ARQUIVOS.values() if not (PASTA_RAW / f).exists()]
    if not faltando:
        print("Arquivos já estão em data/raw — download ignorado.")
        return
    try:
        import kagglehub
        origem = Path(kagglehub.dataset_download("olistbr/brazilian-ecommerce"))
        for f in faltando:
            shutil.copy(origem / f, PASTA_RAW / f)
        print("Baixado do Kaggle.")
    except Exception as erro:
        print(f"Kaggle indisponível ({erro.__class__.__name__}); usando espelho do GitHub...")
        import ssl
        try:
            import certifi  # evita erro de certificado SSL em alguns Macs
            contexto = ssl.create_default_context(cafile=certifi.where())
        except ImportError:
            contexto = ssl.create_default_context()
        for f in faltando:
            with urllib.request.urlopen(ESPELHO + f, context=contexto) as resp:
                (PASTA_RAW / f).write_bytes(resp.read())
        print("Baixado do GitHub.")

baixar_dados()
bruto = {nome: pd.read_csv(PASTA_RAW / arq) for nome, arq in ARQUIVOS.items()}
pd.DataFrame({"tabela": list(bruto), "linhas": [len(d) for d in bruto.values()],
              "colunas": [d.shape[1] for d in bruto.values()]})
""")

md("""
## 3. Perfil dos dados (antes da limpeza)
Antes de mexer em qualquer coisa: quantos nulos e duplicados existem em cada tabela?
""")

code("""
# ---------- 3. Profiling ----------
perfil = []
for nome, df in bruto.items():
    nulos = df.isna().sum()
    perfil.append({
        "tabela": nome,
        "linhas": len(df),
        "linhas_duplicadas": int(df.duplicated().sum()),
        "colunas_com_nulos": int((nulos > 0).sum()),
        "pct_celulas_nulas": round(100 * nulos.sum() / df.size, 2),
    })
perfil = pd.DataFrame(perfil)
perfil
""")

code("""
# Detalhe dos nulos nas tabelas principais
for nome in ["orders", "products", "order_reviews"]:
    n = bruto[nome].isna().sum()
    print(f"\\n{nome}:\\n{n[n > 0].to_string()}")

print("\\nStatus dos pedidos:\\n", bruto["orders"]["order_status"].value_counts().to_string())
print("\\nReviews com review_id repetido:", bruto["order_reviews"]["review_id"].duplicated().sum())
print("Pedidos com mais de uma review:", bruto["order_reviews"]["order_id"].duplicated().sum())
""")

md("""
## 4. Limpeza (camada silver)
Principais problemas encontrados e o tratamento aplicado:

| Problema | Tratamento |
|---|---|
| Datas lidas como texto | Conversão para `datetime` |
| CEP perdendo o zero à esquerda (`1310` em vez de `01310`) | CEP como texto com 5 dígitos |
| Cidades com e sem acento / caixa misturada | Remoção de acentos e padronização em minúsculas |
| Colunas com erro de digitação (`product_name_lenght`) | Renomeadas (`product_name_length`) |
| 610 produtos sem categoria | Categoria `sem_categoria` |
| Pedidos com mais de uma avaliação | Mantida só a avaliação mais recente por pedido |
| Pagamentos `not_defined` com valor 0 e parcelas = 0 | Removidos / parcelas ajustadas para 1 |
| Pedido "entregue" sem data de entrega | Mantido, marcado com flag de inconsistência |
""")

code("""
# ---------- 4. Funções de limpeza ----------
def sem_acento(s: pd.Series) -> pd.Series:
    return (s.astype("string").str.strip().str.lower()
             .map(lambda x: unicodedata.normalize("NFKD", x).encode("ascii", "ignore").decode()
                  if isinstance(x, str) else x))

def cep(s: pd.Series) -> pd.Series:
    return s.astype("Int64").astype("string").str.zfill(5)

def datas(df, colunas):
    for c in colunas:
        df[c] = pd.to_datetime(df[c], errors="coerce")
    return df

silver = {}

# Pedidos
o = bruto["orders"].drop_duplicates("order_id").copy()
o = datas(o, ["order_purchase_timestamp", "order_approved_at", "order_delivered_carrier_date",
              "order_delivered_customer_date", "order_estimated_delivery_date"])
o["flag_entrega_inconsistente"] = (o["order_status"].eq("delivered")
                                    & o["order_delivered_customer_date"].isna())
silver["orders"] = o

# Itens
i = bruto["order_items"].drop_duplicates(["order_id", "order_item_id"]).copy()
i = datas(i, ["shipping_limit_date"])
silver["order_items"] = i[(i["price"] > 0) & (i["freight_value"] >= 0)]

# Pagamentos
p = bruto["order_payments"].copy()
p = p[~((p["payment_type"] == "not_defined") & (p["payment_value"] == 0))]
p["payment_installments"] = p["payment_installments"].clip(lower=1)
silver["order_payments"] = p

# Avaliações: 1 por pedido (a mais recente)
r = datas(bruto["order_reviews"].copy(), ["review_creation_date", "review_answer_timestamp"])
r = (r.sort_values("review_answer_timestamp")
      .drop_duplicates("order_id", keep="last")
      .drop_duplicates("review_id", keep="last"))
r["tem_comentario"] = r["review_comment_message"].notna()
silver["order_reviews"] = r

# Clientes e vendedores
c = bruto["customers"].copy()
c["customer_zip_code_prefix"] = cep(c["customer_zip_code_prefix"])
c["customer_city"] = sem_acento(c["customer_city"])
c["customer_state"] = c["customer_state"].str.upper().str.strip()
silver["customers"] = c

s = bruto["sellers"].copy()
s["seller_zip_code_prefix"] = cep(s["seller_zip_code_prefix"])
s["seller_city"] = sem_acento(s["seller_city"])
s["seller_state"] = s["seller_state"].str.upper().str.strip()
silver["sellers"] = s

# Produtos
pr = bruto["products"].rename(columns={
    "product_name_lenght": "product_name_length",
    "product_description_lenght": "product_description_length",
}).copy()
pr["product_category_name"] = pr["product_category_name"].fillna("sem_categoria")
silver["products"] = pr

silver["category_translation"] = bruto["category_translation"].copy()

pd.DataFrame({"tabela": list(silver),
              "linhas_antes": [len(bruto[t]) for t in silver],
              "linhas_depois": [len(d) for d in silver.values()]})
""")

md("""
## 5. Testes de qualidade
Se alguma regra falhar, o notebook para aqui — nada de dado ruim chegando no banco.
""")

code("""
# ---------- 5. Validações ----------
def checar(condicao, mensagem):
    status = "✅" if condicao else "❌"
    print(f"{status} {mensagem}")
    assert condicao, mensagem

checar(silver["orders"]["order_id"].is_unique, "order_id único em pedidos")
checar(silver["customers"]["customer_id"].is_unique, "customer_id único em clientes")
checar(silver["products"]["product_id"].is_unique, "product_id único em produtos")
checar(silver["order_reviews"]["order_id"].is_unique, "no máximo 1 avaliação por pedido")
checar(silver["order_items"]["order_id"].isin(silver["orders"]["order_id"]).all(), "todo item pertence a um pedido")
checar(silver["orders"]["customer_id"].isin(silver["customers"]["customer_id"]).all(), "todo pedido tem cliente")
checar(silver["order_items"]["product_id"].isin(silver["products"]["product_id"]).all(), "todo item tem produto")
checar((silver["order_items"]["price"] > 0).all(), "preços positivos")
checar(silver["order_reviews"]["review_score"].between(1, 5).all(), "notas entre 1 e 5")
checar(silver["customers"]["customer_zip_code_prefix"].str.len().eq(5).all(), "CEPs com 5 dígitos")
""")

md("""
## 6. Carga no DuckDB
- `bronze`: CSV original, sem nenhuma alteração (rastreabilidade)
- `silver`: tabelas limpas acima

Depois é só abrir `data/olist.duckdb` no **DBeaver** para explorar com SQL.
""")

code("""
# ---------- 6. Carga ----------
ARQUIVO_DB.unlink(missing_ok=True)
con = duckdb.connect(str(ARQUIVO_DB))
con.execute("CREATE SCHEMA bronze; CREATE SCHEMA silver;")

for nome, arq in ARQUIVOS.items():
    con.execute(f"CREATE TABLE bronze.{nome} AS SELECT * FROM read_csv_auto('{(PASTA_RAW / arq).as_posix()}', all_varchar=true)")

for nome, df in silver.items():
    con.register("tmp_df", df)
    con.execute(f"CREATE TABLE silver.{nome} AS SELECT * FROM tmp_df")
    con.unregister("tmp_df")

resumo = con.execute(\"\"\"
    SELECT schema_name AS camada, table_name AS tabela, estimated_size AS linhas
    FROM duckdb_tables() ORDER BY 1, 2
\"\"\").df()
con.close()
resumo
""")

md("""
## 7. Próximos passos
1. `cd dbt && dbt build` → cria a camada **gold** (fatos, dimensões e tabelas do dashboard) e roda os testes.
2. Abrir `data/olist.duckdb` no DBeaver e rodar `sql/analises.sql`.
3. `python scripts/exportar_tableau.py` → gera os CSVs usados no Tableau.
""")

code("""
# Em Colab: baixar o banco para usar no dbt/DBeaver do seu computador
if EM_COLAB:
    from google.colab import files
    files.download(str(ARQUIVO_DB))
""")

nb = {
    "cells": cells,
    "metadata": {
        "colab": {"provenance": []},
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python"},
    },
    "nbformat": 4,
    "nbformat_minor": 5,
}
for n, c in enumerate(nb["cells"]):
    c["id"] = f"cell-{n:02d}"
destino = Path(__file__).resolve().parents[1] / "notebooks" / "01_ingestao_limpeza.ipynb"
destino.write_text(json.dumps(nb, ensure_ascii=False, indent=1), encoding="utf-8")
print("Notebook gerado:", destino)
