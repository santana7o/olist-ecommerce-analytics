"""
Gera o XML das planilhas, painéis e navegação do dashboard do Tableau (3 páginas).
É usado por scripts/montar_twbx.py, que injeta este XML no pacote base criado pelo Tableau Public
(o pacote base guarda a conexão com o Excel da camada gold e a extração .hyper).
"""
import sys
import uuid
from pathlib import Path
from xml.sax.saxutils import quoteattr

sys.path.insert(0, str(Path(__file__).parent))
import layout_dashboard as L  # noqa: E402

DS = "federated.olist"  # substituído pelo nome real da fonte de dados
SIMPLE_ID = True

COLUNAS = {
    "pedido_id": "string", "data_compra": "date", "ano": "integer", "mes": "integer", "nome_mes": "string",
    "dia_semana": "string", "uf": "string", "estado": "string", "regiao": "string", "cliente_unico_id": "string",
    "categoria_principal": "string", "forma_pagamento_principal": "string", "qtd_itens": "integer",
    "valor_produtos": "real", "valor_frete": "real", "receita": "real", "nota": "integer",
    "dias_para_entrega": "integer", "dias_de_atraso": "integer", "entregue_no_prazo": "integer",
}


# ---------------------------------------------------------------- campos calculados
def milhar(expr):
    """Formata um inteiro com ponto de milhar (ex.: 97.905)."""
    return f"STR(INT(({expr})/1000)) + '.' + RIGHT('000' + STR(({expr}) % 1000), 3)"


def dec(expr, casas=1):
    return f"REPLACE(STR(ROUND({expr}, {casas})), '.', ',')"


def pct(cond):
    return dec(f"SUM(IF {cond} THEN 1 ELSE 0 END) / COUNT([pedido_id]) * 100") + " + '%'"


CARTAO = "[forma_pagamento_principal] = 'Cartão de crédito'"

# nome interno -> (legenda, fórmula, tipo, papel)
CALCULOS = {
    # Visão geral
    "Calculation_receita_txt": ("Receita (texto)", "'R$ ' + " + dec("SUM([receita])/1000000") + " + ' mi'", "string", "dimension"),
    "Calculation_pedidos_txt": ("Pedidos (texto)", milhar("COUNT([pedido_id])"), "string", "dimension"),
    "Calculation_ticket_txt": ("Ticket médio (texto)", "'R$ ' + " + dec("SUM([receita])/COUNT([pedido_id])", 2), "string", "dimension"),
    "Calculation_prazo_txt": ("% no prazo (texto)", dec("AVG([entregue_no_prazo])*100") + " + '%'", "string", "dimension"),
    "Calculation_nota_txt": ("Nota média (texto)", dec("AVG([nota])", 2), "string", "dimension"),
    "Calculation_dias_txt": ("Prazo médio (texto)", dec("AVG([dias_para_entrega])") + " + ' dias'", "string", "dimension"),
    "Calculation_frete_txt": ("Frete / receita (texto)", dec("SUM([valor_frete])/SUM([receita])*100") + " + '%'", "string", "dimension"),
    "Calculation_receita_mil": ("Receita (R$ mil)", "ROUND(SUM([receita])/1000, 0)", "real", "measure"),
    "Calculation_nota_media": ("Nota média", "ROUND(AVG([nota]), 2)", "real", "measure"),
    "Calculation_prazo_medio": ("Prazo médio (dias)", "ROUND(AVG([dias_para_entrega]), 1)", "real", "measure"),
    # Logística
    "Calculation_atrasados_txt": ("Pedidos com atraso (texto)", milhar("SUM(IF [dias_de_atraso] > 0 THEN 1 ELSE 0 END)"), "string", "dimension"),
    "Calculation_atraso_medio_txt": ("Atraso médio (texto)", dec("AVG(IF [dias_de_atraso] > 0 THEN [dias_de_atraso] END)") + " + ' dias'", "string", "dimension"),
    "Calculation_nota_no_prazo_txt": ("Nota sem atraso (texto)", dec("AVG(IF [dias_de_atraso] <= 0 THEN [nota] END)", 2), "string", "dimension"),
    "Calculation_nota_atraso7_txt": ("Nota +7 dias (texto)", dec("AVG(IF [dias_de_atraso] > 7 THEN [nota] END)", 2), "string", "dimension"),
    "Calculation_prazo_nordeste_txt": ("No prazo Nordeste (texto)", dec("AVG(IF [regiao] = 'Nordeste' THEN [entregue_no_prazo] END)*100") + " + '%'", "string", "dimension"),
    "Calculation_faixa_atraso": ("Faixa de atraso",
        "IF ISNULL([dias_de_atraso]) THEN 'Não entregue' ELSEIF [dias_de_atraso] <= 0 THEN 'No prazo' "
        "ELSEIF [dias_de_atraso] <= 3 THEN '1 a 3 dias' ELSEIF [dias_de_atraso] <= 7 THEN '4 a 7 dias' "
        "ELSE '+ de 7 dias' END", "string", "dimension"),
    "Calculation_ordem_faixa": ("Ordem da faixa",
        "IF ISNULL([dias_de_atraso]) THEN 9 ELSEIF [dias_de_atraso] <= 0 THEN 1 ELSEIF [dias_de_atraso] <= 3 THEN 2 "
        "ELSEIF [dias_de_atraso] <= 7 THEN 3 ELSE 4 END", "integer", "measure"),
    "Calculation_ordem_dia": ("Ordem do dia da semana", "(DATEPART('weekday', [data_compra]) + 5) % 7 + 1", "integer", "measure"),
    # Clientes
    "Calculation_clientes_txt": ("Clientes (texto)", milhar("COUNTD([cliente_unico_id])"), "string", "dimension"),
    "Calculation_pedidos_cliente": ("Pedidos por cliente", "{ FIXED [cliente_unico_id] : COUNT([pedido_id]) }", "integer", "measure"),
    "Calculation_recompra_txt": ("Taxa de recompra (texto)",
        dec("COUNTD(IF [Calculation_pedidos_cliente] > 1 THEN [cliente_unico_id] END) / COUNTD([cliente_unico_id]) * 100") + " + '%'",
        "string", "dimension"),
    "Calculation_cartao_txt": ("% cartão (texto)", pct(CARTAO), "string", "dimension"),
    "Calculation_boleto_txt": ("% boleto (texto)", pct("[forma_pagamento_principal] = 'Boleto'"), "string", "dimension"),
    "Calculation_ticket_cartao_txt": ("Ticket cartão (texto)",
        "'R$ ' + " + dec(f"SUM(IF {CARTAO} THEN [receita] END) / SUM(IF {CARTAO} THEN 1 END)", 2), "string", "dimension"),
    "Calculation_sp_txt": ("% pedidos SP (texto)", pct("[uf] = 'SP'"), "string", "dimension"),
}


def uuid_de(texto):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, "olist-" + texto)).upper()


def sid(texto, recuo=6):
    return f"\n{' ' * recuo}<simple-id uuid='{{{uuid_de(texto)}}}' />" if SIMPLE_ID else ""


def coluna_calc(n, recuo):
    cap, f, t, papel = CALCULOS[n]
    esp = " " * recuo
    tipo = "quantitative" if papel == "measure" else "nominal"
    return (f"{esp}<column caption={quoteattr(cap)} datatype='{t}' name='[{n}]' role='{papel}' type='{tipo}'>\n"
            f"{esp}  <calculation class='tableau' formula={quoteattr(f)} />\n{esp}</column>")


def colunas_calculadas(recuo=6):
    return "\n".join(coluna_calc(n, recuo) for n in CALCULOS)


def estilo_cores_datasource():
    return f"""      <style>
        <style-rule element='mark'>
          <encoding attr='color' field='[yr:data_compra:ok]' type='palette'>
            <map to='{L.COR_2017}'>
              <bucket>2017</bucket>
            </map>
            <map to='{L.COR_2018}'>
              <bucket>2018</bucket>
            </map>
          </encoding>
        </style-rule>
      </style>"""


# ---------------------------------------------------------------- planilhas
def ref(inst):
    return f"[{DS}].[{inst}]"


def deps(*itens):
    """itens: (coluna, derivação, tipo, nome_da_instância)"""
    cols, inst, vistos = [], [], set()
    for col, der, tipo, nome in itens:
        if col not in vistos:
            vistos.add(col)
            if col in CALCULOS:
                cols.append(coluna_calc(col, 12))
            else:
                t = COLUNAS[col]
                papel = "measure" if t in ("real", "integer") else "dimension"
                tp = "quantitative" if papel == "measure" else ("ordinal" if t == "date" else "nominal")
                cols.append(f"            <column datatype='{t}' name='[{col}]' role='{papel}' type='{tp}' />")
        inst.append(f"            <column-instance column='[{col}]' derivation='{der}' name='[{nome}]' pivot='key' type='{tipo}' />")
    return (f"          <datasource-dependencies datasource='{DS}'>\n" + "\n".join(cols) + "\n"
            + "\n".join(inst) + "\n          </datasource-dependencies>")


def worksheet(nome, dependencias, painel, linhas="", colunas="", estilo="", extras_view=""):
    return f"""    <worksheet name={quoteattr(nome)}>
      <table>
        <view>
          <datasources>
            <datasource caption='Pedidos Olist (gold)' name='{DS}' />
          </datasources>
{dependencias}
{extras_view}          <aggregation value='true' />
        </view>
        <style>
{estilo}
        </style>
        <panes>
{painel}
        </panes>
        <rows>{linhas}</rows>
        <cols>{colunas}</cols>
      </table>{sid(nome)}
    </worksheet>"""


def planilha_texto(nome, calc, fundo, cor, tamanho, largura, altura):
    inst = f"usr:{calc}:nk"
    estilo = f"""          <style-rule element='table'>
            <format attr='background-color' value='{fundo}' />
          </style-rule>
          <style-rule element='cell'>
            <format attr='width' value='{largura}' />
            <format attr='height' value='{altura}' />
            <format attr='text-align' value='center' />
            <format attr='vertical-align' value='center' />
          </style-rule>"""
    painel = f"""          <pane selection-relaxation-option='selection-relaxation-allow'>
            <view>
              <breakdown value='auto' />
            </view>
            <mark class='Text' />
            <encodings>
              <text column='{ref(inst)}' />
            </encodings>
            <customized-label>
              <formatted-text>
                <run bold='true' fontcolor='{cor}' fontsize='{tamanho}'>&lt;{ref(inst)}&gt;</run>
              </formatted-text>
            </customized-label>
            <style>
              <style-rule element='mark'>
                <format attr='mark-labels-show' value='true' />
                <format attr='mark-color' value='{fundo}' />
              </style-rule>
            </style>
          </pane>"""
    return worksheet(nome, deps((calc, "User", "nominal", inst)), painel, estilo=estilo)


def estilo_grafico(eixo_valor, escopo_valor, esconder="cols", largura_celula=None, formato_valor=None, altura_celula=None):
    s = f"""          <style-rule element='axis'>
            <format attr='title' class='0' field='{ref(eixo_valor)}' scope='{escopo_valor}' value='' />
          </style-rule>
          <style-rule element='worksheet'>
            <format attr='display-field-labels' scope='{esconder}' value='false' />
            <format attr='show-null-value-warning' value='false' />
          </style-rule>
          <style-rule element='gridline'>
            <format attr='line-visibility' value='off' />
          </style-rule>"""
    celula = []
    if largura_celula:
        celula.append(f"<format attr='width' value='{largura_celula}' />")
    if altura_celula:
        celula.append(f"<format attr='height' value='{altura_celula}' />")
    if formato_valor:
        celula.append(f"<format attr='text-format' field='{ref(eixo_valor)}' value='{formato_valor}' />")
    if celula:
        s += "\n          <style-rule element='cell'>\n" + "\n".join("            " + c for c in celula) + "\n          </style-rule>"
    return s


def painel_marcas(classe, cor=None, cor_campo=None, rotulos=False, extra=None):
    enc = (f"\n            <encodings>\n              <color column='{ref(cor_campo)}' />\n            </encodings>"
           if cor_campo else "")
    formatos = []
    if cor:
        formatos.append(f"<format attr='mark-color' value='{cor}' />")
    if rotulos:
        formatos.append("<format attr='mark-labels-show' value='true' />")
    if extra:
        formatos.append(extra)
    estilo = ""
    if formatos:
        corpo = "\n".join("                " + f for f in formatos)
        estilo = (f"\n            <style>\n              <style-rule element='mark'>\n{corpo}\n"
                  f"              </style-rule>\n            </style>")
    return f"""          <pane selection-relaxation-option='selection-relaxation-allow'>
            <view>
              <breakdown value='auto' />
            </view>
            <mark class='{classe}' />{enc}{estilo}
          </pane>"""


def graf_receita_mensal():
    mes, ordem, ano, rec = "none:nome_mes:nk", "min:mes:qk", "yr:data_compra:ok", "usr:Calculation_receita_mil:qk"
    larg = (L.area_principal(True)[2] - 60) // 12
    return worksheet(
        "Receita mensal",
        deps(("nome_mes", "None", "nominal", mes), ("mes", "Min", "quantitative", ordem),
             ("data_compra", "Year", "ordinal", ano), ("Calculation_receita_mil", "User", "quantitative", rec)),
        painel_marcas("Line", cor_campo=ano, extra="<format attr='mark-markers-mode' value='all' />"),
        linhas=ref(rec), colunas=ref(mes),
        estilo=estilo_grafico(rec, "rows", largura_celula=larg),
        extras_view=f"          <sort class='computed' column='{ref(mes)}' direction='ASC' using='{ref(ordem)}' />\n")


def graf_barras(nome, dim, dim_der, dim_inst, med, med_der, med_inst, horizontal, cor, sort_by=None,
                sort_dir="DESC", filtro="", rotulos=False, formato=None, slices="", n=10, area=None):
    itens = [(dim, dim_der, "nominal" if dim_der == "None" else "ordinal", dim_inst),
             (med, med_der, "quantitative", med_inst)]
    extras = filtro
    if sort_by:
        if sort_by[3] != med_inst:
            itens.append(sort_by)
        extras += f"          <sort class='computed' column='{ref(dim_inst)}' direction='{sort_dir}' using='{ref(sort_by[3])}' />\n"
    extras += slices
    linhas, colunas = (ref(dim_inst), ref(med_inst)) if horizontal else (ref(med_inst), ref(dim_inst))
    return worksheet(
        nome, deps(*itens), painel_marcas("Bar", cor=cor, rotulos=rotulos),
        linhas=linhas, colunas=colunas,
        estilo=estilo_grafico(med_inst, "cols" if horizontal else "rows",
                              esconder="rows" if horizontal else "cols", formato_valor=formato,
                              largura_celula=None if horizontal else (area[2] - 60) // n,
                              altura_celula=(area[3] - 40) // n if horizontal else None),
        extras_view=extras)


USER_NS = "xmlns:user='http://www.tableausoftware.com/xml/user'"


def filtro_top10(dim_inst, expressao, n=10):
    return f"""          <filter class='categorical' column='{ref(dim_inst)}'>
            <groupfilter count='{n}' end='top' function='end' units='records' user:ui-marker='end' user:ui-top-by-field='true'>
              <groupfilter direction='DESC' expression={quoteattr(expressao)} function='order' user:ui-marker='order'>
                <groupfilter function='level-members' level='[{dim_inst}]' user:ui-enumeration='all' user:ui-marker='enumerate' />
              </groupfilter>
            </groupfilter>
          </filter>
"""


def filtro_excluir(dim_inst, membro):
    return f"""          <filter class='categorical' column='{ref(dim_inst)}'>
            <groupfilter function='except' user:ui-domain='database' user:ui-enumeration='exclusive' user:ui-marker='enumerate'>
              <groupfilter function='level-members' level='[{dim_inst}]' />
              <groupfilter function='member' level='[{dim_inst}]' member={quoteattr('"' + membro + '"')} />
            </groupfilter>
          </filter>
"""


def fatias(dim_inst):
    return f"          <slices>\n            <column>{ref(dim_inst)}</column>\n          </slices>\n"


NOMES_GRAFICOS = ["Receita mensal", "Receita por UF", "Nota por atraso", "Prazo por regiao", "Top categorias", "Pedidos por dia"]


def graficos():
    rec = ("Calculation_receita_mil", "User", "quantitative", "usr:Calculation_receita_mil:qk")
    faixa = "none:Calculation_faixa_atraso:nk"
    cat = "none:categoria_principal:nk"
    ordem_faixa = ("Calculation_ordem_faixa", "Min", "quantitative", "min:Calculation_ordem_faixa:qk")
    prazo = ("Calculation_prazo_medio", "User", "quantitative", "usr:Calculation_prazo_medio:qk")
    return [
        graf_receita_mensal(),
        graf_barras("Receita por UF", "uf", "None", "none:uf:nk", rec[0], rec[1], rec[3], False, L.AMARELO,
                    sort_by=rec, filtro=filtro_top10("none:uf:nk", "SUM([receita])", 12), slices=fatias("none:uf:nk"),
                    rotulos=True, formato="#,##0", n=12, area=L.area_lateral()),
        graf_barras("Nota por atraso", "Calculation_faixa_atraso", "None", faixa, "Calculation_nota_media", "User", "usr:Calculation_nota_media:qk",
                    False, L.AMARELO, sort_by=ordem_faixa, sort_dir="ASC",
                    filtro=filtro_excluir(faixa, "Não entregue"), slices=fatias(faixa), rotulos=True,
                    formato="#,##0.00", n=4, area=L.area_principal()),
        graf_barras("Prazo por regiao", "regiao", "None", "none:regiao:nk", prazo[0], prazo[1], prazo[3], True,
                    L.AMARELO, sort_by=prazo, rotulos=True, formato="#,##0.0", n=5, area=L.area_lateral()),
        graf_barras("Top categorias", "categoria_principal", "None", cat, rec[0], rec[1], rec[3], True, L.AZUL_2,
                    sort_by=rec, filtro=filtro_top10(cat, "SUM([receita])"), slices=fatias(cat), rotulos=True,
                    formato="#,##0", n=10, area=L.area_principal()),
        graf_barras("Pedidos por dia", "dia_semana", "None", "none:dia_semana:nk", "pedido_id", "Count",
                    "cnt:pedido_id:qk", False, L.AMARELO, rotulos=True, formato="#,##0", n=7, area=L.area_lateral(),
                    sort_by=("Calculation_ordem_dia", "Min", "quantitative", "min:Calculation_ordem_dia:qk"), sort_dir="ASC"),
    ]


# ---------------------------------------------------------------- textos (KPIs e tiles)
def planilhas_texto():
    """Retorna {chave: (nome_planilha, xml)}"""
    saida = {}
    for pagina in L.PAGINAS:
        c = L.CONTEUDO[pagina]
        for i, (_, calc) in enumerate(c["kpis"]):
            chave = ("KPI", calc)
            if chave not in saida:
                _, _, w, h = L.area_kpi(i)
                nome = "KPI · " + CALCULOS[calc][0].replace(" (texto)", "")
                saida[chave] = (nome, planilha_texto(nome, calc, "#ffffff", L.TEXTO, 32, w - 4, h - 4))
        for i, (_, calc) in enumerate(c["tiles"]):
            chave = ("Tile", calc, i)
            if chave not in saida:
                _, _, w, h = L.area_tile(i)
                nome = "Tile · " + CALCULOS[calc][0].replace(" (texto)", "")
                saida[chave] = (nome, planilha_texto(nome, calc, L.TILE_CORES[i], "#ffffff", 24, w - 4, h - 4))
    return saida


# ---------------------------------------------------------------- painéis e navegação
def u(v, total):
    return round(v / total * 100000)


def zona(zid, nome, box):
    x, y, w, h = box
    return (f"        <zone h='{u(h, L.H)}' id='{zid}' name={quoteattr(nome)} show-title='false' "
            f"w='{u(w, L.W)}' x='{u(x, L.W)}' y='{u(y, L.H)}' />")


def botao(zid, destino, box):
    x, y, w, h = box
    alvo = uuid_de("w-dash-" + destino)
    return f"""        <zone h='{u(h, L.H)}' id='{zid}' type-v2='dashboard-object' w='{u(w, L.W)}' x='{u(x, L.W)}' y='{u(y, L.H)}'>
          <button action='tabdoc:goto-sheet window-id=&quot;{{{alvo}}}&quot;' button-type='text'>
            <button-visual-state>
              <caption>{destino.upper()}</caption>
              <button-caption-font-style fontcolor='#ffffff' fontname='Tableau Bold' fontsize='11' />
              <format attr='background-color' value='#ffffff00' />
            </button-visual-state>
          </button>
        </zone>"""


def dashboards(textos):
    saida, visoes = [], {}
    for pagina in L.PAGINAS:
        c = L.CONTEUDO[pagina]
        zonas = ["        <zone h='100000' id='1' type-v2='layout-basic' w='100000' x='0' y='0' />",
                 f"        <zone h='100000' id='2' is-scaled='1' param='Image/fundo_{L.slug(pagina)}.png' type-v2='bitmap' w='100000' x='0' y='0' />"]
        itens = [(textos[("KPI", calc)][0], L.area_kpi(i)) for i, (_, calc) in enumerate(c["kpis"])]
        itens += [(textos[("Tile", calc, i)][0], L.area_tile(i)) for i, (_, calc) in enumerate(c["tiles"])]
        itens += [(c["principal"][1], L.area_principal(c["legenda"])), (c["lateral"][1], L.area_lateral())]
        zid = 3
        for nome, box in itens:
            zonas.append(zona(zid, nome, box))
            zid += 1
        for destino, box in L.ABAS.items():
            zonas.append(botao(zid, destino, box))
            zid += 1
        visoes[pagina] = [n for n, _ in itens]
        saida.append(f"""    <dashboard name={quoteattr(pagina)}>
      <style />
      <size maxheight='{L.H}' maxwidth='{L.W}' minheight='{L.H}' minwidth='{L.W}' sizing-mode='fixed' />
      <zones>
{chr(10).join(zonas)}
      </zones>{sid('dash-' + pagina)}
    </dashboard>""")
    return "\n".join(saida), visoes


def janelas(planilhas, visoes):
    ws = "\n".join(f"""    <window class='worksheet' hidden='true' maximized='true' name={quoteattr(n)}>
      <cards>
        <edge name='left'>
          <strip size='160'>
            <card type='pages' />
            <card type='filters' />
            <card type='marks' />
          </strip>
        </edge>
        <edge name='top'>
          <strip size='2147483647'>
            <card type='columns' />
          </strip>
          <strip size='2147483647'>
            <card type='rows' />
          </strip>
        </edge>
      </cards>{sid('w-' + n)}
    </window>""" for n in planilhas)
    ds = "\n".join(f"""    <window class='dashboard' {"maximized='true' " if i == 0 else ""}name={quoteattr(p)}>
      <viewpoints>
{chr(10).join(f"        <viewpoint name={quoteattr(v)} />" for v in visoes[p])}
      </viewpoints>
      <active id='-1' />{sid('w-dash-' + p)}
    </window>""" for i, p in enumerate(L.PAGINAS))
    return f"  <windows source-height='30'>\n{ds}\n{ws}\n  </windows>"


def montar_xml():
    """Retorna worksheets + dashboards + windows como texto XML."""
    textos = planilhas_texto()
    planilhas = [x for _, x in textos.values()] + graficos()
    nomes = [n for n, _ in textos.values()] + NOMES_GRAFICOS
    dash, visoes = dashboards(textos)
    return (f"  <worksheets>\n{chr(10).join(planilhas)}\n  </worksheets>\n"
            f"  <dashboards>\n{dash}\n  </dashboards>\n{janelas(nomes, visoes)}")
