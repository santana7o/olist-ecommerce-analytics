"""
Gera os fundos (layout) das 3 páginas do dashboard: faixa azul, cards brancos, tiles amarelos,
rótulos, ícones e o anel (donut) do 4º indicador. Os números e gráficos vêm do Tableau.

Uso: python scripts/gerar_fundo_dashboard.py
"""
import sys
from pathlib import Path

import pandas as pd
from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, str(Path(__file__).parent))
import layout_dashboard as L  # noqa: E402

BASE = Path(__file__).resolve().parents[1]
S = 2  # desenha em 2x e reduz (bordas suaves)
FUNDO = (240, 242, 246)
CINZA = (120, 128, 145)


def rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def fonte(tam, negrito=False):
    nome = "Carlito-Bold.ttf" if negrito else "Carlito-Regular.ttf"
    for pasta in ["/usr/share/fonts/truetype/crosextra/", "/usr/share/fonts/truetype/carlito/"]:
        if Path(pasta + nome).exists():
            return ImageFont.truetype(pasta + nome, tam * S)
    return ImageFont.truetype("DejaVuSans-Bold.ttf" if negrito else "DejaVuSans.ttf", tam * S)


def r(box):
    x, y, w, h = box
    return [x * S, y * S, (x + w) * S, (y + h) * S]


def percentuais():
    df = pd.read_csv(BASE / "tableau" / "dados" / "mart_pedidos_dashboard.csv")
    return {
        "pct_no_prazo": df["entregue_no_prazo"].mean(),
        "pct_frete": df["valor_frete"].sum() / df["receita"].sum(),
        "pct_cartao": (df["forma_pagamento_principal"] == "Cartão de crédito").mean(),
    }


def desenhar(pagina, pct):
    c = L.CONTEUDO[pagina]
    img = Image.new("RGB", (L.W * S, L.H * S), FUNDO)
    d = ImageDraw.Draw(img)

    # faixa azul em degradê + linha amarela
    alt = 205
    a1, a2 = rgb(L.AZUL_1), rgb(L.AZUL_2)
    for yy in range(alt * S):
        t = yy / (alt * S)
        d.line([(0, yy), (L.W * S, yy)], fill=tuple(int(a1[i] + (a2[i] - a1[i]) * t) for i in range(3)))
    d.rectangle([0, alt * S, L.W * S, (alt + 4) * S], fill=rgb(L.AMARELO))

    # sombras
    sombra = Image.new("L", img.size, 0)
    ds = ImageDraw.Draw(sombra)
    for box in L.KPIS + [L.PRINCIPAL, L.LATERAL] + L.TILES:
        x0, y0, x1, y1 = r(box)
        ds.rounded_rectangle([x0, y0 + 6 * S, x1, y1 + 6 * S], 14 * S, fill=60)
    sombra = sombra.filter(ImageFilter.GaussianBlur(10 * S))
    img = Image.composite(Image.new("RGB", img.size, (170, 176, 190)), img, sombra)
    d = ImageDraw.Draw(img)

    for box in L.KPIS + [L.PRINCIPAL, L.LATERAL]:
        d.rounded_rectangle(r(box), 14 * S, fill=(255, 255, 255))
    for box, cor in zip(L.TILES, L.TILE_CORES):
        d.rounded_rectangle(r(box), 14 * S, fill=rgb(cor))

    # logo + título
    x, y = 60, 34
    d.rounded_rectangle([x * S, y * S, (x + 40) * S, (y + 40) * S], 9 * S, fill=(255, 255, 255))
    for i, hh in enumerate([14, 24, 32]):
        bx = x + 8 + i * 9
        d.rectangle([bx * S, (y + 34 - hh) * S, (bx + 6) * S, (y + 34) * S],
                    fill=rgb(L.AMARELO) if i == 2 else rgb(L.AZUL_2))
    d.text(((x + 54) * S, (y - 2) * S), "Olist E-commerce", font=fonte(24, True), fill="white")
    d.text(((x + 54) * S, (y + 26) * S), c["subtitulo"], font=fonte(14), fill=(200, 212, 240))

    # aba ativa (contorno); os textos das abas são botões do Tableau
    ax, ay, aw, ah = L.ABAS[pagina]
    d.rounded_rectangle([ax * S, ay * S, (ax + aw) * S, (ay + ah) * S], 6 * S, outline="white", width=2 * S)

    def centro(txt, box, dy, f, cor):
        bx, by, bw, _ = box
        tw = d.textlength(txt, font=f) / S
        d.text(((bx + (bw - tw) / 2) * S, (by + dy) * S), txt, font=f, fill=cor)

    for i, (rot, _) in enumerate(c["kpis"]):
        b = L.KPIS[i] if i < 3 else (L.KPIS[i][0], L.KPIS[i][1], L.KPIS[i][2] - 100, L.KPIS[i][3])
        centro(rot, b, 16, fonte(13), CINZA)
    centro(c["principal"][0], L.PRINCIPAL, 18, fonte(17), (70, 78, 95))
    centro(c["lateral"][0], L.LATERAL, 18, fonte(17), (70, 78, 95))
    for (rot, _), box in zip(c["tiles"], L.TILES):
        centro(rot, box, 96, fonte(15, True), (255, 255, 255))

    # ícones dos tiles
    for box, simb in zip(L.TILES, c["icones"]):
        bx, by, _, _ = box
        cx, cy, rr = bx + 34, by + 36, 18
        d.ellipse([(cx - rr) * S, (cy - rr) * S, (cx + rr) * S, (cy + rr) * S], outline="white", width=2 * S)
        f = ImageFont.truetype("DejaVuSans-Bold.ttf", 17 * S)
        tw = d.textlength(simb, font=f) / S
        d.text(((cx - tw / 2) * S, (cy - 11) * S), simb, font=f, fill="white")

    # donut do 4º KPI
    cx, cy = L.DONUT["centro"]
    rr, esp = L.DONUT["raio"], 11
    caixa = [(cx - rr) * S, (cy - rr) * S, (cx + rr) * S, (cy + rr) * S]
    d.ellipse(caixa, outline=(236, 238, 242), width=esp * S)
    d.arc(caixa, -90, -90 + 360 * pct[c["donut"]], fill=rgb(L.AMARELO), width=esp * S)

    # legenda (gráfico de linhas)
    if c["legenda"]:
        px, py, pw, ph = L.PRINCIPAL
        lx, ly = px + pw / 2 - 70, py + ph - 30
        for i, (ano, cor) in enumerate([("2017", L.COR_2017), ("2018", L.COR_2018)]):
            x0 = lx + i * 80
            d.line([(x0 * S, (ly + 8) * S), ((x0 + 22) * S, (ly + 8) * S)], fill=rgb(cor), width=3 * S)
            d.ellipse([(x0 + 7) * S, (ly + 4) * S, (x0 + 15) * S, (ly + 12) * S], fill="white", outline=rgb(cor), width=2 * S)
            d.text(((x0 + 28) * S, ly * S), ano, font=fonte(13), fill=CINZA)

    d.text((60 * S, 872 * S), "Fonte: Brazilian E-Commerce Public Dataset by Olist (Kaggle) · Pipeline: Colab + Python → DuckDB → dbt → Tableau",
           font=fonte(11), fill=(140, 146, 160))
    return img.resize((L.W, L.H), Image.LANCZOS)


def main():
    pct = percentuais()
    pasta = BASE / "tableau" / "assets"
    pasta.mkdir(parents=True, exist_ok=True)
    for p in L.PAGINAS:
        destino = pasta / f"fundo_{L.slug(p)}.png"
        desenhar(p, pct).save(destino)
        print("Fundo salvo:", destino.relative_to(BASE))


if __name__ == "__main__":
    main()
