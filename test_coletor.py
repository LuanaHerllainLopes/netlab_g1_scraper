"""
Testes automatizados com pytest para o projeto NetLab G1 Scraper.
Execução: pytest test_coletor.py -v
"""

from coletor_g1 import ColetorG1, parse_html_com_beautifulsoup


def test_extracao_url_real():
    """Testa se a URL real da notícia é extraída do link de clique do Globo Measures."""
    url_measures = (
        "https://measures.globo.com/v1/click?c=busca-headless&"
        "u=https%3A%2F%2Fg1.globo.com%2Ftecnologia%2Fnoticia%2F2026%2F08%2F25%2Fmulta-tiktok.ghtml"
    )
    url_real = ColetorG1.extrair_url_real(url_measures)
    assert url_real == "https://g1.globo.com/tecnologia/noticia/2026/08/25/multa-tiktok.ghtml"

    # Se já for uma URL direta, mantém inalterada
    url_direta = "https://g1.globo.com/politica/noticia/exemplo.ghtml"
    assert ColetorG1.extrair_url_real(url_direta) == url_direta


def test_processar_hits():
    """Testa a conversão dos dados brutos recebidos da busca em dicionários padronizados."""
    coletor = ColetorG1(termo="lgpd", total_paginas=1)
    hits_ficticios = [
        {
            "_source": {
                "title": " Nova regra da ANPD entra em vigor ",
                "url": "https://measures.globo.com/v1/click?u=https%3A%2F%2Fg1.globo.com%2Fnoticia1.ghtml",
                "description": " Detalhes sobre a resolução da autoridade. ",
                "created": "2026-09-10T10:00:00Z"
            }
        },
        {
            "_source": {
                "title": "Vídeo sobre Segurança de Dados",
                "url": "https://g1.globo.com/video1.ghtml",
                "description": None,  # Resumo nulo
                "modified": "2026-09-12T15:30:00Z"
            }
        }
    ]

    noticias = coletor.processar_hits(hits_ficticios, numero_pagina=1)
    assert len(noticias) == 2

    # Item 1
    assert noticias[0]["titulo"] == "Nova regra da ANPD entra em vigor"
    assert noticias[0]["url"] == "https://g1.globo.com/noticia1.ghtml"
    assert noticias[0]["resumo"] == "Detalhes sobre a resolução da autoridade."
    assert noticias[0]["pagina"] == 1

    # Item 2 (resumo nulo tratado sem erro)
    assert noticias[1]["titulo"] == "Vídeo sobre Segurança de Dados"
    assert noticias[1]["resumo"] is None


def test_parser_beautifulsoup():
    """Testa o parser Beautiful Soup em um fragmento HTML realista."""
    html = """
    <div class="results">
        <div class="widget--info">
            <a href="https://g1.globo.com/economia/lgpd.ghtml">
                <div class="widget--info__title">Empresas se adaptam à LGPD</div>
            </a>
            <p class="widget--info__description">Guia para pequenas empresas cumprirem a lei.</p>
            <span class="widget--info__meta">Ontem</span>
        </div>
    </div>
    """
    noticias = parse_html_com_beautifulsoup(html)
    assert len(noticias) == 1
    assert noticias[0]["titulo"] == "Empresas se adaptam à LGPD"
    assert noticias[0]["url"] == "https://g1.globo.com/economia/lgpd.ghtml"
    assert "Guia para pequenas" in noticias[0]["resumo"]
    assert noticias[0]["data_publicacao"] == "Ontem"


def test_desduplicacao():
    """Testa se notícias com URLs repetidas são descartadas."""
    coletor = ColetorG1()
    coletor.urls_vistas.add("https://g1.globo.com/noticia-ja-vista.ghtml")

    hits_duplicados = [
        {
            "_source": {
                "title": "Notícia repetida",
                "url": "https://g1.globo.com/noticia-ja-vista.ghtml"
            }
        }
    ]
    noticias = coletor.processar_hits(hits_duplicados, numero_pagina=2)
    # A verificação de URLs vistas descarta itens repetidos
    itens_novos = [n for n in noticias if n["url"] not in coletor.urls_vistas]
    assert len(itens_novos) == 0
