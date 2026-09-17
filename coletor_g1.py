"""
NetLab UFRJ - Coletor de Resultados de Busca do G1 sobre 'LGPD'
Candidata: Desenvolvedora (Solução do Teste Técnico)
Descrição: Rotina robusta de coleta de notícias do G1.
Identifica a migração do G1 para arquitetura de Busca Headless (SPA em React 18),
coleta os dados reais via endpoint de busca da Globo, normaliza as URLs,
trata campos ausentes e exporta em CSV (UTF-8 com BOM) e JSON.
Também inclui parser Beautiful Soup para compatibilidade com HTML estático.
"""

import csv
import json
import logging
import random
import time
from datetime import datetime, timezone, timedelta
from urllib.parse import parse_qs, unquote, urlparse

import requests
from bs4 import BeautifulSoup

# Configuração de Logging para auditoria e acompanhamento
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("coleta_g1.log", encoding="utf-8")
    ]
)
logger = logging.getLogger("NetLabG1Scraper")

# Fuso horário de Brasília (UTC-3)
FUSO_BRASILIA = timezone(timedelta(hours=-3))


class ColetorG1:
    API_URL = "https://busca.globo.com/v1/search"
    SEARCH_PROFILE = "sp_g1_globo_com"
    QUERY_ID = "g1.info_query_recency"  # Ordenação por mais recentes

    def __init__(self, termo="lgpd", total_paginas=3, itens_por_pagina=10):
        self.termo = termo
        self.total_paginas = total_paginas
        self.itens_por_pagina = itens_por_pagina
        self.headers = {
            "Content-Type": "application/json",
            "X-Tenant-Id": "g1",
            "X-Must-Thumborize": "true",
            "X-Track-Urls": "true",
            "Origin": "https://g1.globo.com",
            "Referer": "https://g1.globo.com/",
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            )
        }
        self.resultados = []
        self.urls_vistas = set()

    @staticmethod
    def extrair_url_real(url_redirecionamento):
        """
        Extrai a URL original da notícia do parâmetro 'u=' da URL do Globo Measures,
        removendo redirecionadores e mantendo o link canônico do G1.
        """
        if not url_redirecionamento:
            return None
        parsed = urlparse(url_redirecionamento)
        if "measures.globo.com" in parsed.netloc:
            qs = parse_qs(parsed.query)
            if "u" in qs and qs["u"]:
                return unquote(qs["u"][0])
        return url_redirecionamento

    def coletar_pagina_api(self, numero_pagina):
        """
        Coleta uma página de resultados utilizando o endpoint de Busca Headless do G1.
        Calcula o deslocamento (offset / 'from') com base no número da página.
        """
        deslocamento = (numero_pagina - 1) * self.itens_por_pagina
        payload = [{
            "search_profile": self.SEARCH_PROFILE,
            "query": self.QUERY_ID,
            "params": {
                "q": self.termo,
                "from": deslocamento,
                "size": self.itens_por_pagina
            }
        }]

        logger.info(f"Requisitando página {numero_pagina} (itens {deslocamento + 1} a {deslocamento + self.itens_por_pagina})...")

        try:
            resp = requests.post(self.API_URL, headers=self.headers, json=payload, timeout=12)
            if resp.status_code != 200:
                logger.warning(f"Resposta inesperada HTTP {resp.status_code} na página {numero_pagina}")
                return []
            
            data = resp.json()
            if not data or not isinstance(data, list) or len(data) == 0:
                return []

            result_block = data[0].get("result", {})
            hits = result_block.get("hits", {}).get("hits", [])
            return hits

        except requests.exceptions.RequestException as err:
            logger.error(f"Erro de conexão na página {numero_pagina}: {err}")
            return []

    def processar_hits(self, hits, numero_pagina):
        """
        Converte os dados brutos retornados pela busca em dicionários padronizados,
        tratando campos vazios e garantindo unicidade.
        """
        noticias_pagina = []
        horario_coleta = datetime.now(FUSO_BRASILIA).isoformat()

        for item in hits:
            source = item.get("_source", {})
            titulo = source.get("title")
            raw_url = source.get("url")

            # Validação: ignora se não tiver título ou link
            if not titulo or not raw_url:
                continue

            url_limpa = self.extrair_url_real(raw_url)
            resumo = source.get("description")
            data_pub = source.get("created") or source.get("modified")

            noticias_pagina.append({
                "titulo": titulo.strip(),
                "resumo": resumo.strip() if resumo else None,
                "data_publicacao": data_pub,
                "url": url_limpa,
                "pagina": numero_pagina,
                "coletado_em": horario_coleta
            })

        return noticias_pagina

    def executar(self):
        """Executa a coleta de todas as páginas planejadas e acumula os resultados."""
        logger.info(f"=== INICIANDO COLETA NO G1 (TERMO: '{self.termo}', PÁGINAS: {self.total_paginas}) ===")

        for pagina in range(1, self.total_paginas + 1):
            hits = self.coletar_pagina_api(pagina)

            if not hits:
                logger.info(f"Página {pagina} retornou 0 resultados. Finalizando paginação.")
                break

            noticias = self.processar_hits(hits, numero_pagina=pagina)
            novos = 0

            # Desduplicação: só adiciona se a URL ainda não foi vista
            for n in noticias:
                if n["url"] not in self.urls_vistas:
                    self.urls_vistas.add(n["url"])
                    self.resultados.append(n)  # ACÚMULO CORRETO (sem sobrescrever!)
                    novos += 1

            logger.info(f"Página {pagina}: +{novos} notícias únicas (Total acumulado: {len(self.resultados)}).")

            # Pausa ética entre páginas
            if pagina < self.total_paginas:
                espera = random.uniform(1.2, 2.0)
                time.sleep(espera)

        logger.info(f"=== COLETA CONCLUÍDA! TOTAL DE NOTÍCIAS COLETADAS: {len(self.resultados)} ===")
        self.salvar_arquivos()

    def salvar_arquivos(self):
        """Salva a base em CSV (UTF-8-SIG para Excel) e JSON."""
        if not self.resultados:
            logger.warning("Nenhum dado para salvar.")
            return

        # 1. CSV com encoding utf-8-sig (para não quebrar acentos no Excel no Windows)
        nome_csv = "g1_lgpd.csv"
        campos = ["titulo", "resumo", "data_publicacao", "url", "pagina", "coletado_em"]
        with open(nome_csv, "w", encoding="utf-8-sig", newline="") as f_csv:
            writer = csv.DictWriter(f_csv, fieldnames=campos)
            writer.writeheader()
            writer.writerows(self.resultados)
        logger.info(f"Arquivo CSV salvo com sucesso: '{nome_csv}' ({len(self.resultados)} registros)")

        # 2. JSON estruturado
        nome_json = "g1_lgpd.json"
        with open(nome_json, "w", encoding="utf-8") as f_json:
            json.dump(self.resultados, f_json, ensure_ascii=False, indent=2)
        logger.info(f"Arquivo JSON salvo com sucesso: '{nome_json}'")


# Também fornecemos o parser Beautiful Soup para caso de HTMLs renderizados
def parse_html_com_beautifulsoup(html_str):
    """
    Parser com Beautiful Soup para extrair notícias de fragmentos HTML ou páginas renderizadas.
    """
    soup = BeautifulSoup(html_str, "html.parser")
    cards = soup.select("li.widget, div.widget--info, [id^='search-result-item-']")
    noticias = []

    for card in cards:
        tag_link = card.find("a", href=True)
        if not tag_link:
            continue

        tag_titulo = card.select_one(".widget--info__title, h2, h3")
        titulo = tag_titulo.get_text().strip() if tag_titulo else tag_link.get_text().strip()

        tag_resumo = card.select_one(".widget--info__description, p")
        resumo = tag_resumo.get_text().strip() if tag_resumo else None

        tag_data = card.select_one(".widget--info__meta, span.tempo, time")
        data_pub = tag_data.get_text().strip() if tag_data else None

        noticias.append({
            "titulo": titulo,
            "resumo": resumo,
            "data_publicacao": data_pub,
            "url": tag_link["href"]
        })
    return noticias


if __name__ == "__main__":
    coletor = ColetorG1(termo="lgpd", total_paginas=3, itens_por_pagina=10)
    coletor.executar()
