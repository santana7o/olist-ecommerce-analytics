"""
Layout e conteúdo das 3 páginas do dashboard (usado pelo fundo em PNG e pelo workbook do Tableau).
Todas as posições estão em pixels de um painel fixo de 1400 x 900.
"""

W, H = 1400, 900

# ---- Paleta -------------------------------------------------------------------
AZUL_1, AZUL_2 = "#1b3473", "#345eb0"
AMARELO = "#f2b632"
TILE_CORES = ["#f2b632", "#f5c85f", "#f6d27d"]
TEXTO = "#1c2a48"
COR_2017, COR_2018 = "#4e79a7", "#f28e2b"   # cores padrão do Tableau para as duas séries

# ---- Geometria (x, y, w, h) -------------------------------------------------------
KPIS = [(60, 110, 300, 135), (382, 110, 300, 135), (704, 110, 300, 135), (1026, 110, 314, 135)]
PRINCIPAL = (60, 270, 650, 590)
LATERAL = (735, 270, 605, 330)
TILES = [(735, 625, 188, 235), (943, 625, 188, 235), (1152, 625, 188, 235)]
DONUT = dict(centro=(1275, 177), raio=40)

# Área onde o Tableau desenha cada elemento (dentro dos cards)
def area_kpi(i):
    x, y, w, h = KPIS[i]
    return (x + 10, y + 35, (w - 120 if i == 3 else w - 20), h - 45)

def area_principal(com_legenda=False):
    x, y, w, h = PRINCIPAL
    return (x + 20, y + 50, w - 40, h - (95 if com_legenda else 65))

def area_lateral():
    x, y, w, h = LATERAL
    return (x + 20, y + 50, w - 40, h - 65)

def area_tile(i):
    x, y, w, h = TILES[i]
    return (x + 10, y + 130, w - 20, 80)

# ---- Menu de navegação (abas) -----------------------------------------------------
PAGINAS = ["Visão Geral", "Logística", "Clientes"]
ABAS = {  # posição do botão de cada aba (x, y, w, h)
    "Visão Geral": (950, 36, 140, 34),
    "Logística": (1100, 36, 115, 34),
    "Clientes": (1225, 36, 115, 34),
}

# ---- Conteúdo de cada página ------------------------------------------------------
# kpis/tiles: (rótulo, campo calculado do Tableau)
CONTEUDO = {
    "Visão Geral": dict(
        subtitulo="Visão geral de vendas · jan/2017 a ago/2018",
        kpis=[("RECEITA TOTAL", "Calculation_receita_txt"), ("PEDIDOS", "Calculation_pedidos_txt"),
              ("TICKET MÉDIO", "Calculation_ticket_txt"), ("ENTREGAS NO PRAZO", "Calculation_prazo_txt")],
        donut="pct_no_prazo",
        principal=("RECEITA MENSAL (R$ MIL) · 2017 x 2018", "Receita mensal"),
        lateral=("RECEITA POR ESTADO · TOP 12 (R$ MIL)", "Receita por UF"),
        tiles=[("NOTA MÉDIA", "Calculation_nota_txt"), ("PRAZO DE ENTREGA", "Calculation_dias_txt"),
               ("FRETE / RECEITA", "Calculation_frete_txt")],
        icones=["★", "→", "%"],
        legenda=True,
    ),
    "Logística": dict(
        subtitulo="Entrega, atraso e satisfação · jan/2017 a ago/2018",
        kpis=[("PRAZO MÉDIO DE ENTREGA", "Calculation_dias_txt"), ("PEDIDOS COM ATRASO", "Calculation_atrasados_txt"),
              ("ATRASO MÉDIO (ATRASADOS)", "Calculation_atraso_medio_txt"), ("FRETE / RECEITA", "Calculation_frete_txt")],
        donut="pct_frete",
        principal=("NOTA MÉDIA DO CLIENTE POR FAIXA DE ATRASO", "Nota por atraso"),
        lateral=("PRAZO MÉDIO DE ENTREGA POR REGIÃO (DIAS)", "Prazo por regiao"),
        tiles=[("NOTA SEM ATRASO", "Calculation_nota_no_prazo_txt"), ("NOTA COM +7 DIAS", "Calculation_nota_atraso7_txt"),
               ("NO PRAZO · NORDESTE", "Calculation_prazo_nordeste_txt")],
        icones=["✓", "!", "%"],
        legenda=False,
    ),
    "Clientes": dict(
        subtitulo="Clientes, categorias e pagamento · jan/2017 a ago/2018",
        kpis=[("CLIENTES ÚNICOS", "Calculation_clientes_txt"), ("TAXA DE RECOMPRA", "Calculation_recompra_txt"),
              ("NOTA MÉDIA", "Calculation_nota_txt"), ("PAGOS NO CARTÃO", "Calculation_cartao_txt")],
        donut="pct_cartao",
        principal=("TOP 10 CATEGORIAS POR RECEITA (R$ MIL)", "Top categorias"),
        lateral=("PEDIDOS POR DIA DA SEMANA", "Pedidos por dia"),
        tiles=[("PAGOS NO BOLETO", "Calculation_boleto_txt"), ("TICKET NO CARTÃO", "Calculation_ticket_cartao_txt"),
               ("PEDIDOS DE SP", "Calculation_sp_txt")],
        icones=["$", "★", "%"],
        legenda=False,
    ),
}


def slug(pagina):
    import unicodedata
    s = unicodedata.normalize("NFKD", pagina).encode("ascii", "ignore").decode().lower()
    return s.replace(" ", "_")
