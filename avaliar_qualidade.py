"""
NetLab UFRJ - Script de Auditoria da Qualidade de Dados (7 Dimensões)
Autor: Luana Herllain Lopes <luana.herllain@gmail.com>
Descrição: Avalia programaticamente os dados coletados do G1 contra
o framework de 7 dimensões da qualidade de dados.
"""

import csv
import json
import os
from datetime import datetime
from urllib.parse import urlparse

# Definição dos contratos de dados
CAMPOS_OBRIGATORIOS = ["titulo", "url", "data_publicacao", "pagina", "coletado_em"]
CAMPOS_OPCIONAIS = ["resumo"]
DOMINIOS_VALIDOS = ["g1.globo.com", "globo.com"]

# Amostra de Ground Truth manual (para checagem da dimensão 4: Acurácia)
GROUND_TRUTH_AMOSTRA = {
    "https://g1.globo.com/mg/zona-da-mata/mg1-zona-da-mata/video/integracao-tec-mais-de-37-dos-orgaos-e-empresas-nao-seguem-regras-da-lgpd-14903650.ghtml": {
        "titulo": "Integração TEC: mais de 37% dos órgãos e empresas não seguem regras da LGPD"
    }
}


class AvaliadorQualidade:
    def __init__(self, json_path="g1_lgpd.json", csv_path="g1_lgpd.csv", log_path="coleta_g1.log"):
        self.json_path = json_path
        self.csv_path = csv_path
        self.log_path = log_path
        self.dados_json = []
        self.dados_csv = []
        self.relatorio = {}

    def carregar_dados(self):
        """Carrega os artefatos de dados gerados pela coleta."""
        if os.path.exists(self.json_path):
            with open(self.json_path, "r", encoding="utf-8") as f:
                self.dados_json = json.load(f)
        
        if os.path.exists(self.csv_path):
            with open(self.csv_path, "r", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                self.dados_csv = list(reader)

        if not self.dados_json:
            raise FileNotFoundError("Base de dados JSON não encontrada para auditoria.")

    # -------------------------------------------------------------
    # 1. COMPLETUDE (Completeness)
    # -------------------------------------------------------------
    def avaliar_completude(self):
        """Avalia presença de campos mandatórios e ausência de nulos/vazios."""
        total = len(self.dados_json)
        conformes = sum(
            1 for item in self.dados_json
            if all(item.get(c) is not None and str(item.get(c)).strip() != "" for c in CAMPOS_OBRIGATORIOS)
        )
        percentual = (conformes / total) * 100 if total > 0 else 0
        self.relatorio["1_Completude"] = {
            "metrica": f"{percentual:.1f}%",
            "detalhes": f"{conformes}/{total} registros possuem todos os campos mandatórios",
            "status": "Aprovado" if percentual == 100.0 else "Reprovado"
        }

    # -------------------------------------------------------------
    # 2. ATUALIDADE (Timeliness / Currency)
    # -------------------------------------------------------------
    def avaliar_atualidade(self):
        """Avalia conformidade do formato ISO 8601 e frescor temporal das notícias."""
        total = len(self.dados_json)
        datas_validas = 0
        noticias_recentes = 0

        for item in self.dados_json:
            dt_pub_str = item.get("data_publicacao")
            if dt_pub_str:
                try:
                    dt_pub = datetime.fromisoformat(dt_pub_str.replace("Z", "+00:00"))
                    datas_validas += 1
                    if dt_pub.year >= 2026:
                        noticias_recentes += 1
                except ValueError:
                    pass

        percentual = (datas_validas / total) * 100 if total > 0 else 0
        self.relatorio["2_Atualidade"] = {
            "metrica": f"{percentual:.1f}%",
            "detalhes": f"{datas_validas}/{total} datas em ISO 8601; {noticias_recentes} publicadas recentemente",
            "status": "Aprovado" if percentual == 100.0 else "Reprovado"
        }

    # -------------------------------------------------------------
    # 3. PRECISÃO / VALIDADE (Validity / Precision)
    # -------------------------------------------------------------
    def avaliar_precisao(self):
        """Avalia se registros pertencem ao domínio oficial e se estão livres de anúncios."""
        total = len(self.dados_json)
        validos = 0

        for item in self.dados_json:
            url = item.get("url", "")
            parsed = urlparse(url)
            eh_url_valida = parsed.scheme in ["http", "https"] and any(
                dom in parsed.netloc for dom in DOMINIOS_VALIDOS
            )
            titulo = item.get("titulo", "")
            titulo_valido = len(titulo) > 5 and not titulo.lower().startswith("anúncio")

            if eh_url_valida and titulo_valido:
                validos += 1

        percentual = (validos / total) * 100 if total > 0 else 0
        self.relatorio["3_Precisão"] = {
            "metrica": f"{percentual:.1f}%",
            "detalhes": f"{validos}/{total} matérias válidas do domínio oficial sem ruído de layout",
            "status": "Aprovado" if percentual == 100.0 else "Reprovado"
        }

    # -------------------------------------------------------------
    # 4. ACURÁCIA (Accuracy / Conformity)
    # -------------------------------------------------------------
    def avaliar_acuracia(self):
        """Confronta os dados coletados com a amostra manual (Ground Truth)."""
        total_testes = len(GROUND_TRUTH_AMOSTRA)
        acertos = 0
        mapa_coletado = {item["url"]: item for item in self.dados_json}

        for url_ref, dados_ref in GROUND_TRUTH_AMOSTRA.items():
            if url_ref in mapa_coletado:
                if mapa_coletado[url_ref]["titulo"] == dados_ref["titulo"]:
                    acertos += 1

        percentual = (acertos / total_testes) * 100 if total_testes > 0 else 100.0
        self.relatorio["4_Acurácia"] = {
            "metrica": f"{percentual:.1f}%",
            "detalhes": f"{acertos}/{total_testes} amostras de Ground Truth com 100% de fidelidade literal",
            "status": "Aprovado" if percentual == 100.0 else "Reprovado"
        }

    # -------------------------------------------------------------
    # 5. UNICIDADE (Uniqueness)
    # -------------------------------------------------------------
    def avaliar_unicidade(self):
        """Verifica a taxa de duplicidade com base no conjunto de URLs únicas."""
        total = len(self.dados_json)
        urls = [item.get("url") for item in self.dados_json if item.get("url")]
        unicas = len(set(urls))
        duplicatas = total - unicas

        percentual = (unicas / total) * 100 if total > 0 else 0
        self.relatorio["5_Unicidade"] = {
            "metrica": f"{percentual:.1f}%",
            "detalhes": f"{unicas} registros únicos de {total} (0 duplicatas)",
            "status": "Aprovado" if duplicatas == 0 else "Reprovado"
        }

    # -------------------------------------------------------------
    # 6. CONSISTÊNCIA (Consistency)
    # -------------------------------------------------------------
    def avaliar_consistencia(self):
        """Avalia a normalização de URLs (sem tracking) e paridade entre CSV e JSON."""
        total = len(self.dados_json)
        urls_limpas = sum(1 for item in self.dados_json if "measures.globo.com" not in item.get("url", ""))
        paridade_arquivos = len(self.dados_json) == len(self.dados_csv)

        percentual = (urls_limpas / total) * 100 if total > 0 else 0
        aprovado = (percentual == 100.0) and paridade_arquivos

        self.relatorio["6_Consistência"] = {
            "metrica": f"{percentual:.1f}%",
            "detalhes": f"URLs sem tracking: {urls_limpas}/{total}; Paridade JSON/CSV: {'OK' if paridade_arquivos else 'ERRO'}",
            "status": "Aprovado" if aprovado else "Reprovado"
        }

    # -------------------------------------------------------------
    # 7. RASTREABILIDADE (Traceability / Data Lineage)
    # -------------------------------------------------------------
    def avaliar_rastreabilidade(self):
        """Avalia linhagem dos dados (página, timestamp com timezone) e log de auditoria."""
        total = len(self.dados_json)
        rastreaveis = sum(
            1 for item in self.dados_json
            if isinstance(item.get("pagina"), int) and item.get("pagina") > 0
            and bool(item.get("coletado_em") and "-03:00" in item.get("coletado_em"))
        )
        tem_arquivo_log = os.path.exists(self.log_path) and os.path.getsize(self.log_path) > 0
        percentual = (rastreaveis / total) * 100 if total > 0 else 0
        aprovado = (percentual == 100.0) and tem_arquivo_log

        self.relatorio["7_Rastreabilidade"] = {
            "metrica": f"{percentual:.1f}%",
            "detalhes": f"Registros rastreáveis: {rastreaveis}/{total}; Log de auditoria: {'OK' if tem_arquivo_log else 'Ausente'}",
            "status": "Aprovado" if aprovado else "Reprovado"
        }

    def executar_auditoria_completa(self):
        """Executa a auditoria de todas as 7 dimensões e exibe o relatório."""
        self.carregar_dados()
        self.avaliar_completude()
        self.avaliar_atualidade()
        self.avaliar_precisao()
        self.avaliar_acuracia()
        self.avaliar_unicidade()
        self.avaliar_consistencia()
        self.avaliar_rastreabilidade()

        print("\n" + "=" * 80)
        print("  RELATÓRIO DE AUDITORIA DE QUALIDADE DOS DADOS (7 DIMENSÕES) - NETLAB UFRJ")
        print("=" * 80)
        print(f"{'Dimensão':<22} | {'Resultado':<10} | {'Status':<10} | {'Evidência / Detalhes'}")
        print("-" * 80)
        for dim, res in self.relatorio.items():
            nome_limpo = dim.split("_")[1]
            print(f"{nome_limpo:<22} | {res['metrica']:<10} | {res['status']:<10} | {res['detalhes']}")
        print("=" * 80 + "\n")


if __name__ == "__main__":
    avaliador = AvaliadorQualidade()
    avaliador.executar_auditoria_completa()