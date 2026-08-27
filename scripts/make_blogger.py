#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Gera o fragmento HTML para colar num post do Blogger.

Um post do Blogger é HTML *dentro* do template do blogue: não pode trazer
<html>/<head>, e um <style> global entraria em conflito com o tema. Este
script parte de site/geometria_simpletica.html e produz:

  - todo o CSS prefixado por .gs-doc (nada escapa para fora do post);
  - as fontes por @import, em vez de <link> (o Blogger corta <link>);
  - rem convertido em px, para não depender do font-size do tema;
  - o MathJax carregado só se ainda não existir na página;
  - "&" em bruto escapado e sem newlines dentro dos blocos (HTML inválido
    ou quebras de linha fazem o sanitizador do Blogger comer parágrafos);
  - os diagramas em <img> com data URI, porque o editor do Blogger apaga
    SVG inline (--svg-inline mantém-nos inline, para usar noutros sítios;
    --img-base URL grava-os em site/diagramas/ e aponta para lá).

Uso:  python3 scripts/make_blogger.py [--src FICHEIRO] [--out FICHEIRO]
                                    [--svg-inline] [--img-base URL]
      (ou: make blogger)
"""
import base64
import os
import re
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _arg(nome, omissao):
    """--nome valor, com um valor por omissão."""
    return sys.argv[sys.argv.index(nome) + 1] if nome in sys.argv else omissao


ORIGEM = os.path.join(RAIZ, _arg("--src", "site/geometria_simpletica.html"))
DESTINO = os.path.join(RAIZ, _arg("--out", os.path.splitext(
    _arg("--src", "site/geometria_simpletica.html"))[0] + "-blogger.html"))

ROOT = ".gs-doc"
# As minhas regras levam a raiz duplicada; as defesas contra o tema, mais
# abaixo, ficam um degrau de especificidade abaixo destas e um degrau acima
# das do tema. Assim o tema nunca decide nada, e as defesas só preenchem as
# propriedades que eu não declaro.
ROOT2 = ROOT + ROOT
BASE_REM = 17.0          # o html{font-size:17px} do original
# Um @import por família: assim nenhum URL leva "&", e o fragmento fica sem
# um único & em bruto para o sanitizador do Blogger poder estragar.
FONTES = (
    "https://fonts.googleapis.com/css2?family=EB+Garamond:ital,wght@0,400;0,500;0,600;1,400;1,500",
    "https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,500;0,600;1,400;1,600",
    "https://fonts.googleapis.com/css2?family=Cinzel:wght@400;500",
)

# O MathJax só é carregado se a página ainda não o tiver (o template pode já
# trazê-lo). Sem barras duplas nos comentários: o ficheiro fica numa linha só.
MATHJAX = """<script>
(function () {
  if (window.MathJax) { return; }
  window.MathJax = {
    tex: { inlineMath: [['\\\\(', '\\\\)']], displayMath: [['\\\\[', '\\\\]']], tags: 'none' },
    options: { skipHtmlTags: ['script', 'noscript', 'style', 'textarea', 'pre'] }
  };
  var s = document.createElement('script');
  s.src = 'https://cdnjs.cloudflare.com/ajax/libs/mathjax/3.2.2/es5/tex-chtml.min.js';
  s.async = true;
  document.head.appendChild(s);
}());
</script>"""


def rem_para_px(texto):
    """1.2rem -> 20.4px, para o post não depender do font-size do tema."""
    return re.sub(r"(-?\d*\.?\d+)rem",
                  lambda m: "%gpx" % round(float(m.group(1)) * BASE_REM, 2),
                  texto)


def blocos(css):
    """Parte o CSS em (prelúdio, corpo) ao nível de topo, contando chavetas."""
    fora = []
    i = prof = 0
    inicio = 0
    abre = None
    while i < len(css):
        c = css[i]
        if c == "{":
            if prof == 0:
                abre = i
            prof += 1
        elif c == "}":
            prof -= 1
            if prof == 0:
                fora.append((css[inicio:abre].strip(), css[abre + 1:i].strip()))
                inicio = i + 1
        i += 1
    return fora


def prefixar(seletor):
    partes = []
    for s in (p.strip() for p in seletor.split(",")):
        if not s:
            continue
        if s == ":root" or s == "body":
            partes.append(ROOT2)
        elif s == "html":
            partes.append(None)          # descartado: já não há raiz própria
        elif s == "*":
            partes.append(ROOT2 + " *")
        else:
            partes.append(ROOT2 + " " + s)
    return ", ".join(p for p in partes if p)


def scoped(css):
    saida = []
    for seletor, corpo in blocos(css):
        if seletor.startswith("@keyframes"):
            saida.append("%s { %s }" % (seletor.replace("pageIn", "gsPageIn"), corpo))
        elif seletor.startswith("@media"):
            interior = " ".join("%s { %s }" % (prefixar(s), c) for s, c in blocos(corpo))
            saida.append("%s { %s }" % (seletor, interior))
        else:
            novo = prefixar(seletor)
            if not novo:
                continue
            corpo = corpo.replace("min-height: 100vh;", "")
            corpo = corpo.replace("animation: pageIn", "animation: gsPageIn").rstrip().rstrip(";")
            if novo == ROOT2:
                corpo += "; font-size: %gpx" % BASE_REM
            saida.append("%s { %s }" % (novo, corpo))
    return " ".join(saida)


def prefixar_classes(css, corpo):
    """Renomeia todas as classes para gs-*, no CSS e no HTML.

    O .gs-doc à frente dos seletores não chega: se o tema tiver uma classe
    com o mesmo nome que uma das minhas — e tinha, um .centered com
    display:flex e min-height — as propriedades que eu não declaro vêm dele.
    Com os nomes prefixados nenhuma regra do tema pode sequer apanhá-los.
    """
    nomes = set()
    for m in re.finditer(r'class="([^"]+)"', corpo):
        nomes.update(m.group(1).split())
    nomes.discard("gs-doc")
    corpo = re.sub(r'class="([^"]+)"',
                   lambda m: 'class="%s"' % " ".join("gs-" + c for c in m.group(1).split()),
                   corpo)
    for n in sorted(nomes, key=len, reverse=True):
        css = re.sub(r"\.%s(?![\w-])" % re.escape(n), ".gs-" + n, css)
    print("  %d classes prefixadas" % len(nomes))
    return css, corpo


def escapar_content_css(css):
    """Não-ASCII dentro de content: passa a escape CSS (\\2192).

    O Blogger converte o → literal que está no <style> na entidade &#8594;,
    e o CSS não descodifica entidades: ficava esse texto em bruto à frente
    de cada título de secção. Um escape CSS atravessa a conversão incólume.
    """
    def troca(m):
        aspa, valor = m.group(1), m.group(2)
        novo = "".join(c if ord(c) < 128 else "\\%04X " % ord(c) for c in valor)
        return "content: %s%s%s" % (aspa, novo, aspa)

    css, n = re.subn(r"content:\s*(['\"])(.*?)\1", troca, css)
    return css


def escapar_e_comercial(corpo):
    """& em bruto -> &amp;  (o \\begin{smallmatrix}0&1&0...\\end do TeX).

    HTML inválido faz o sanitizador do Blogger deitar fora o parágrafo
    inteiro. Para o MathJax é indiferente: lê o texto já descodificado.
    """
    corpo, n = re.subn(r"&(?!(?:[a-zA-Z][a-zA-Z0-9]{1,10}|#\d{1,6}|#x[0-9a-fA-F]{1,6});)",
                       "&amp;", corpo)
    if n:
        print("  %d '&' em bruto escapados" % n)
    return corpo


def svg_para_img(corpo, base=None):
    """Troca cada <svg> inline por um <img>: data URI, ou ficheiro se houver base.

    O editor do Blogger remove SVG inline ao guardar o post — fica a moldura
    da figura vazia. Um <img> passa intacto. O desenho continua vectorial;
    só os rótulos é que passam a usar a fonte de recurso (Georgia), porque
    um SVG dentro de <img> não tem acesso às fontes da página.

    Com --img-base URL, os desenhos são gravados em site/diagramas/ e o post
    passa a apontar para URL/dN.svg — para o caso de o blogue recusar data URI.
    """
    pasta = os.path.join(RAIZ, "site", "diagramas")
    if base:
        if not os.path.isdir(pasta):
            os.makedirs(pasta)

    contador = [0]

    def troca(m):
        contador[0] += 1
        i = contador[0]
        svg = m.group(0)
        vb = re.search(r'viewBox="0 0 (\d+(?:\.\d+)?) (\d+(?:\.\d+)?)"', svg)
        w, h = (vb.group(1), vb.group(2)) if vb else ("680", "400")
        titulo = re.search(r"<title>(.*?)</title>", svg, re.S)
        alt = re.sub(r"\s+", " ", titulo.group(1)).strip() if titulo else "diagrama"
        alt = alt.replace('"', "'")
        avulso = ('<?xml version="1.0" encoding="UTF-8"?>'
                  + svg.replace('width="100%"', 'width="%s" height="%s"' % (w, h), 1))
        if base:
            nome = "d%d.svg" % i
            open(os.path.join(pasta, nome), "w", encoding="utf-8").write(avulso)
            src = "%s/%s" % (base.rstrip("/"), nome)
        else:
            src = "data:image/svg+xml;base64," + base64.b64encode(
                avulso.encode("utf-8")).decode("ascii")
        return ('<img src="%s" width="%s" height="%s" alt="%s" '
                'style="display:block;width:100%%;height:auto;border:0">' % (src, w, h, alt))

    corpo, n = re.subn(r"<svg\b.*?</svg>", troca, corpo, flags=re.S)
    print("  %d diagramas em <img> (%s)" % (n, "ficheiros em site/diagramas/" if base
                                            else "data URI"))
    return corpo


def main():
    if not os.path.exists(ORIGEM):
        sys.exit("não encontro %s" % ORIGEM)
    src = open(ORIGEM, encoding="utf-8").read()

    css = re.search(r"<style>(.*?)</style>", src, re.S).group(1)
    corpo = re.search(r"<body>(.*?)</body>", src, re.S).group(1)
    # o rem->px tem de correr ANTES do base64: em base64 pode aparecer, por
    # acaso, um "123rem", e a substituição estragaria o data URI
    corpo = rem_para_px(corpo.strip())
    corpo = escapar_e_comercial(corpo)
    css, corpo = prefixar_classes(css, corpo)
    if "--svg-inline" not in sys.argv:
        base = None
        if "--img-base" in sys.argv:
            base = sys.argv[sys.argv.index("--img-base") + 1]
        corpo = svg_para_img(corpo, base)

    css = "%s\n%s" % (" ".join("@import url('%s');" % u for u in FONTES), scoped(css))
    css = escapar_content_css(css)
    # defesas contra o tema do blogue: bordas, fundos e espaçamentos que os
    # templates costumam impor a svg, figure e div e que atravessariam o post.
    # Defesas contra o tema: preenchem o que eu não declaro (o tema tinha um
    # .centered com display:flex e min-height que inchava as fórmulas), mas
    # ficam abaixo das minhas regras, que levam mais uma classe na raiz.
    d = ROOT2
    css += (
        " {r} {{ max-width: 100%; }}"
        " {d} div, {d} p, {d} figure, {d} figcaption, {d} h1, {d} h2, {d} h3 {{"
        " display: block; min-height: 0; max-width: none; float: none; clear: none;"
        " letter-spacing: inherit; text-indent: 0; text-shadow: none; }}"
        " {d} span, {d} em, {d} strong {{ display: inline; }}"
        " {d} svg, {d} img {{ border: 0; background: transparent; max-width: 100%;"
        " height: auto; box-shadow: none; }}"
        " {d} figure:not([class]) {{ border: 0; background: none; }}"
        # margens da folha em função da largura da coluna do post, e não da
        # janela: há temas do Blogger com colunas de 600px
        " {d} .gs-page {{ padding: 48px clamp(18px, 7%, 85px); }}"
        " {d} .gs-page::before {{ left: clamp(13px, 5%, 68px); }}"
    ).format(r=ROOT, d=d)

    frag = ('<!-- Geometria Simplectica - Luis Ferreira - colar na vista HTML do Blogger -->'
            '<style>%s</style><div class="gs-doc">%s</div>%s'
            % (rem_para_px(css), corpo, MATHJAX))

    # sem newlines dentro dos blocos (o Blogger converte-os em <br>), mas com
    # uma quebra antes de cada folha: linhas de 76 KB tornam a colagem frágil,
    # e um <br> solto entre folhas não faz mal nenhum
    frag = re.sub(r"\s*\n\s*", " ", frag).strip()
    frag = frag.replace('<div class="page"', '\n<div class="page"')
    frag = frag.replace("</div><script>", "</div>\n<script>")

    open(DESTINO, "w", encoding="utf-8").write(frag + "\n")
    print("escrito %s (%.1f KB)" % (DESTINO, len(frag) / 1024.0))


if __name__ == "__main__":
    main()
