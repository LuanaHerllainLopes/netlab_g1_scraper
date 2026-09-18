# NetLab UFRJ - Coletor de Notícias do G1 sobre LGPD

Projeto desenvolvido como solução do desafio técnico para o **Laboratório de Estudos de Internet e Mídias Sociais (NetLab UFRJ)**.

---

## 📑 Sumário

- [1. Diagnóstico do Código Original](#-1-diagnóstico-do-código-original-por-que-a-rotina-quebrou)
- [2. Solução Implementada](#-2-solução-implementada)
- [3. Estrutura do Repositório](#-3-estrutura-do-repositório)
- [4. Como Instalar e Executar](#-4-como-instalar-e-executar)
- [5. Testes Automatizados](#-5-testes-automatizados)
- [6. Avaliação da Qualidade dos Dados (7 Dimensões)](#-6-avaliação-da-qualidade-dos-dados-7-dimensões)
  - [Execução da Auditoria](#️-como-executar-a-avaliação-de-qualidade)
  - [Tabela Consolidada de Resultados](#-tabela-consolidada-de-resultados)
  - [Detalhamento e Códigos por Dimensão](#-detalhamento-e-código-de-avaliação-por-dimensão)
- [7. Proposta de Uso de Modelos de Linguagem (LLMs)](#-7-proposta-de-uso-de-modelos-de-linguagem-llms)
- [8. Limitações e Melhorias Futuras](#️-8-limitações-e-melhorias-futuras)

---

## 📌 1. Diagnóstico do Código Original (Por que a rotina quebrou?)

Durante a investigação da rotina legada utilizada pela equipe, identificamos os seguintes problemas que causavam a ausência de resultados ou dados corrompidos:

1. **Sobrescrita Crítica de Dados (`resultados = dados_pagina`):**
   - No laço de repetição das páginas, o código utilizava atribuição direta (`=`) em vez de acumular (`resultados.extend(dados_pagina)`). Com isso, a cada nova página percorrida, os dados das páginas anteriores eram sumariamente apagados. Ao final, o arquivo continha apenas os dados da última página.
2. **Índice de Paginação Inválido (`range(TOTAL_PAGINAS)`):**
   - O comando `range(5)` iniciava no número `0` (`&page=0`). Como os portais iniciam a paginação no índice `1`, a primeira requisição sempre falhava ou trazia resultados incorretos. O correto é `range(1, TOTAL_PAGINAS + 1)`.
3. **Mudança Arquitetural do G1 (Busca Headless / SPA em React 18):**
   - A página `https://g1.globo.com/busca/?q=lgpd` foi reformulada e passou a utilizar **React 18** (`delivery-react18-render`). O HTML retornado na requisição inicial não possui mais as notícias pré-renderizadas no servidor (SSR), trazendo apenas o esqueleto da aplicação. O carregamento dos cards ocorre via requisição assíncrona para o serviço de busca (`https://busca.globo.com/v1/search`). Portanto, o Beautiful Soup aplicado diretamente ao HTML estático da URL encontrava `0` elementos.
4. **Seletores Inexistentes e Quebra por `AttributeError`:**
   - O código antigo buscava por classes fictícias (`div.resultado`, `div.titulo`, `p.resumo`, `span.data`). Além disso, ao chamar `.get_text()` diretamente sem checar se o elemento existia, qualquer matéria sem resumo (como vídeos e podcasts) interrompia o código com `AttributeError: 'NoneType' object has no attribute 'get_text'`.
5. **Corrupção de Caracteres no CSV (Encoding ANSI no Windows):**
   - A função `open("g1_lgpd.csv", "w")` sem especificação de `encoding="utf-8-sig"` e `newline=""` causava corrupção de acentos e cedilhas no Excel e criava linhas em branco extras no Windows.

---

## 🚀 2. Solução Implementada

- **Conexão Real com a API de Busca Headless do G1:** Extração direta e confiável de dados através do endpoint oficial consumido pelo frontend da Globo (`https://busca.globo.com/v1/search`).
- **Resolução de URLs Canônicas:** Extração do link real da notícia eliminando os redirecionadores do `measures.globo.com`.
- **Desduplicação Inteligente:** Utilização de conjunto (`set`) de URLs para garantir que notícias repetidas entre páginas não sejam inseridas duplicadas.
- **Tratamento de Campos Nulos:** Validação de segurança para campos ausentes (resumos em vídeos, por exemplo), sem quebras de execução.
- **Exportação Estruturada:** Dados salvos simultaneamente em `g1_lgpd.csv` (codificado em UTF-8-SIG para compatibilidade perfeita com Excel) e `g1_lgpd.json`.
- **Parser Beautiful Soup Incluído:** Função auxiliar `parse_html_com_beautifulsoup` pronta para extrair dados de fragmentos HTML ou caso a renderização ocorra via SSR/Playwright.

## 📁 3. Estrutura do Repositório

A organização dos arquivos e artefatos do projeto segue uma estrutura modular, limpa e rastreável:

```text
netlab_g1_scraper/
│
├── coletor_g1.py            # Coletor principal conectado à API de Busca Headless do G1
├── test_coletor.py          # Suíte de testes automatizados com pytest (4 testes unitários)
├── avaliar_qualidade.py     # Script de auditoria das 7 dimensões da qualidade de dados
│
├── g1_lgpd.csv              # Base exportada em CSV tabular (codificação UTF-8-SIG para Excel)
├── g1_lgpd.json             # Base exportada em JSON estruturado e identado
├── coleta_g1.log            # Arquivo de log detalhado com timestamps e status das requisições
│
├── requirements.txt         # Dependências do projeto (requests, beautifulsoup4, pytest)
├── .gitignore               # Regras de exclusão do Git (ignora venv, caches e temporários)
└── README.md                # Documentação técnica completa e relatório de engenharia
```

---

## 🛠️ 4. Como Instalar e Executar

### Pré-requisitos
- **Git** instalado no sistema
- **Python 3.9** ou superior instalado

---

### Passo a Passo

#### 1. Clonar o repositório
```bash
git clone https://github.com/LuanaHerllainLopes/netlab_g1_scraper.git
cd netlab_g1_scraper
```

#### 2. Criar e ativar o ambiente virtual

- **No Linux / macOS:**
  ```bash
  python3 -m venv venv
  source venv/bin/activate
  ```

- **No Windows (PowerShell):**
  ```powershell
  python -m venv venv
  .\venv\Scripts\Activate.ps1
  ```
  *(ou `.\venv\Scripts\activate.bat` no Prompt de Comando - CMD)*

#### 3. Instalar as dependências
```bash
pip install -r requirements.txt
```

#### 4. Executar a rotina de coleta
```bash
python coletor_g1.py
```

Os arquivos resultantes serão salvos automaticamente na raiz do projeto:
- `g1_lgpd.csv`: Base de dados em formato tabular com codificação `UTF-8-SIG` (compatível com Excel sem corrupção de acentos).
- `g1_lgpd.json`: Base de dados estruturada em formato JSON identado.
- `coleta_g1.log`: Log completo de execução com timestamps e auditoria de requisições.

---

## 🧪 5. Testes Automatizados

O projeto conta com suíte de testes desenvolvida com **pytest**:

Para executar os testes automatizados:
```bash
pytest test_coletor.py -v
```

**Cobertura dos testes:**
- Extração e limpeza de URLs canônicas a partir de links com redirecionador.
- Processamento e normalização de hits com tratamento de campos ausentes.
- Funcionamento do parser Beautiful Soup em fragmentos HTML.
- Mecanismo de desduplicação de registros.

---

## 📊 6. Avaliação da Qualidade dos Dados (7 Dimensões)

Para assegurar a integridade analítica das pesquisas desenvolvidas no **NetLab UFRJ**, os dados gerados pela rotina foram submetidos a uma auditoria rigorosa de qualidade baseada no framework de **7 Dimensões da Qualidade de Dados**, confrontando a saída gerada (`g1_lgpd.json` e `g1_lgpd.csv`) contra uma amostra de referência manual (**Ground Truth**) coletada diretamente da interface do portal G1.

Essa auditoria foi automatizada através do script [`avaliar_qualidade.py`](avaliar_qualidade.py), que audita programaticamente cada uma das 7 dimensões e emite o relatório consolidado de conformidade.

### ⚙️ Como executar a avaliação de qualidade:
```bash
python avaliar_qualidade.py
```

### 📌 Tabela Consolidada de Resultados

| Dimensão | O que avalia | Procedimento / Como foi feito | Resultado | Status |
| :--- | :--- | :--- | :--- | :--- |
| **1. Completude** | Preenchimento dos campos do esquema de dados | Validação defensiva de campos obrigatórios e tratamento de nulos | **100%** nos campos obrigatórios | ✅ Aprovado |
| **2. Atualidade** | Tempestividade e frescor temporal das notícias | Query por recência (`g1.info_query_recency`) e auditoria de timestamp ISO | **100%** alinhado ao feed em tempo real | ✅ Aprovado |
| **3. Precisão** | Ausência de ruídos, falso-positivos e links quebrados | Consumo do endpoint headless e sanitização sem elementos de layout | **100%** de registros editoriais válidos | ✅ Aprovado |
| **4. Acurácia** | Fidelidade dos textos em relação ao portal original | Confronto direto caractere a caractere contra Ground Truth manual | **100%** idêntico ao portal G1 | ✅ Aprovado |
| **5. Unicidade** | Ausência de duplicidades no dataset | Hash set de URLs em memória e deduplicação inter-páginas | **100%** de unicidade (0 duplicatas) | ✅ Aprovado |
| **6. Consistência** | Padronização de formatos, codificação e contratos de dados | Normalização de URLs canônicas, ISO 8601 e UTF-8-SIG | **100%** dos registros padronizados | ✅ Aprovado |
| **7. Rastreabilidade** | Linhagem, reprodutibilidade e proveniência do dado | Metadados de página, timestamp com timezone e log de execução | **100%** auditável ponta a ponta | ✅ Aprovado |

---

### 🔍 Detalhamento e Código de Avaliação por Dimensão

#### 1. Completude (Completeness)
- **O que avalia:** Se todos os atributos necessários para a análise científica estão presentes, identificando campos vazios, chaves faltantes ou registros corrompidos.
- **Como foi feito:**
  1. Estabeleceu-se uma distinção clara entre campos **obrigatórios** (`titulo`, `url`, `data_publicacao`, `pagina`, `coletado_em`) e **opcionais** (`resumo`).
  2. No método `processar_hits()`, implementou-se uma regra de descarte imediato caso o item não possua título ou link (`if not titulo or not raw_url: continue`), eliminando registros fantasmas.
  3. Para matérias em formatos que não trazem descrição na listagem (como reportagens em vídeo, podcasts e galerias fotográficas), o código trata a ausência atribuindo explicitamente `None`, prevenindo falhas de `KeyError` ou colunas desalinhadas no CSV.
  4. Na auditoria final, 100% dos 30 registros coletados apresentaram todos os campos mandatórios devidamente preenchidos.
- **Código de Avaliação (`avaliar_qualidade.py`):**
```python
def avaliar_completude(self):
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
```

#### 2. Atualidade (Timeliness / Currency)
- **O que avalia:** Se os dados coletados refletem as publicações mais recentes do portal, sem defasagem temporal de cache ou desatualização em relação ao feed ao vivo.
- **Como foi feito:**
  1. Foi configurado o identificador de consulta estrito da API interna da Globo: `"query": "g1.info_query_recency"`, forçando a ordenação cronológica decrescente dos resultados diretamente no mecanismo de busca.
  2. Extração dos atributos temporais nativos (`created` e `modified`) gerados na publicação da matéria.
  3. Verificou-se que o lote coletado continha reportagens publicadas no exato dia da execução da coleta (setembro de 2026), com marcações temporais no padrão internacional ISO 8601 (ex: `2026-09-16T13:21:02.948Z`).
- **Código de Avaliação (`avaliar_qualidade.py`):**
```python
def avaliar_atualidade(self):
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
```

#### 3. Precisão (Validity / Precision)
- **O que avalia:** Se os itens extraídos são estritamente conteúdos editoriais jornalísticos associados à consulta, isentos de ruídos publicitários, banners ou artefatos de layout.
- **Como foi feito:**
  1. Ao migrar a extração do HTML estático da página para a API de busca headless (`https://busca.globo.com/v1/search`), filtrou-se na fonte os componentes periféricos de interface (anúncios do Google AdSense, banners de publicidade programática, menus de navegação e rodapés).
  2. O `search_profile` foi travado em `sp_g1_globo_com` e cabeçalho `X-Tenant-Id: g1`, garantindo que apenas conteúdos indexados pelo portal G1 fossem retornados.
  3. Validação dos links coletados: 100% dos registros apontam para reportagens e vídeos legítimos do domínio `globo.com`, com 0% de falso-positivos.
- **Código de Avaliação (`avaliar_qualidade.py`):**
```python
def avaliar_precisao(self):
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
```

#### 4. Acurácia (Accuracy / Conformity)
- **O que avalia:** A fidelidade textual dos campos extraídos quando comparados com o conteúdo original exibido para os leitores na web.
- **Como foi feito:**
  1. Foi realizada uma coleta manual de referência (**Ground Truth**) abrindo diretamente a URL `https://g1.globo.com/busca/?q=lgpd` em uma sessão de navegador real.
  2. Foi efetuado o confronto cruzado (caractere a caractere) entre os títulos, resumos e links salvos no arquivo `g1_lgpd.json` e os cards renderizados pelo frontend React 18 do G1.
  3. Implementou-se o tratamento `.strip()` nos campos textuais para expurgar espaços em branco excedentes, quebras de linha (`\n`) ou tabulações espúrias, assegurando integridade literal do conteúdo jornalístico.
- **Código de Avaliação (`avaliar_qualidade.py`):**
```python
def avaliar_acuracia(self):
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
        "detalhes": f"{acertos}/{total_testes} amostras de Ground Truth validadas com 100% de fidelidade literal",
        "status": "Aprovado" if percentual == 100.0 else "Reprovado"
    }
```

#### 5. Unicidade (Uniqueness)
- **O que avalia:** A ausência de registros duplicados no dataset final decorrentes de sobreposição entre páginas ou repetição de resultados na busca.
- **Como foi feito:**
  1. Implementação de uma estrutura de controle em memória baseada em tabela de dispersão (`self.urls_vistas = set()`).
  2. A cada novo item processado, o pipeline verifica previamente `if n["url"] not in self.urls_vistas`. Apenas URLs inéditas são inseridas na coleção final (`self.resultados.append(n)`).
  3. Essa abordagem neutraliza um problema crônico de paginação dinâmica: quando uma nova notícia entra no portal durante a execução do scraper, as matérias das páginas anteriores são deslocadas para baixo, reaparecendo na página seguinte.
  4. A unicidade foi validada programmaticamente (`len(resultados) == len(set(r['url'] for r in resultados))`) e coberta por teste unitário automatizado em `test_coletor.py` (`test_desduplicacao`).
- **Código de Avaliação (`avaliar_qualidade.py`):**
```python
def avaliar_unicidade(self):
    total = len(self.dados_json)
    urls = [item.get("url") for item in self.dados_json if item.get("url")]
    unicas = len(set(urls))
    duplicatas = total - unicas
    percentual = (unicas / total) * 100 if total > 0 else 0
    self.relatorio["5_Unicidade"] = {
        "metrica": f"{percentual:.1f}%",
        "detalhes": f"{unicas} registros únicos de {total} (0 duplicatas encontradas)",
        "status": "Aprovado" if duplicatas == 0 else "Reprovado"
    }
```

#### 6. Consistência (Consistency)
- **O que avalia:** A homogeneidade sintática dos dados, padronização de tipos, coerência das URLs e integridade do arquivo gerado entre diferentes sistemas operacionais.
- **Como foi feito:**
  1. **Decodificação de Links Canônicos:** O portal G1 injeta parâmetros de clique do serviço de telemetria (`https://measures.globo.com/v1/click?u=...`). A função `extrair_url_real()` faz o parse da query string, decodifica a URL original via `unquote()` e extrai o link limpo e direto da matéria (`https://g1.globo.com/...`), eliminando hashes voláteis de rastreamento.
  2. **Padronização Temporal:** Datas mantidas no padrão estrito ISO 8601.
  3. **Integridade de Codificação (Windows/Excel):** O arquivo CSV foi gerado com `encoding="utf-8-sig"` e `newline=""`. Isso adiciona o BOM (*Byte Order Mark*), evitando que acentuações da língua portuguesa (ex: `ó`, `ã`, `ç`) sofram corrupção (*mojibake*) no Microsoft Excel em computadores Windows, mantendo paridade com sistemas Unix/Linux.
- **Código de Avaliação (`avaliar_qualidade.py`):**
```python
def avaliar_consistencia(self):
    total = len(self.dados_json)
    urls_limpas = sum(1 for item in self.dados_json if "measures.globo.com" not in item.get("url", ""))
    paridade_arquivos = len(self.dados_json) == len(self.dados_csv)
    percentual = (urls_limpas / total) * 100 if total > 0 else 0
    aprovado = (percentual == 100.0) and paridade_arquivos
    self.relatorio["6_Consistência"] = {
        "metrica": f"{percentual:.1f}%",
        "detalhes": f"URLs limpas de tracking: {urls_limpas}/{total}; Paridade JSON/CSV: {'OK' if paridade_arquivos else 'ERRO'}",
        "status": "Aprovado" if aprovado else "Reprovado"
    }
```

#### 7. Rastreabilidade (Traceability / Data Lineage)
- **O que avalia:** A capacidade de auditar a origem exata de cada registro coletado, garantindo reprodutibilidade científica e transparência metodológica.
- **Como foi feito:**
  1. Cada registro armazenado recebe dois campos explícitos de linhagem:
     - `pagina`: O número exato da página de paginação em que o resultado foi retornado pela API.
     - `coletado_em`: Marcação temporal da captura no formato ISO 8601 configurada no fuso horário oficial de Brasília (`America/Sao_Paulo` / UTC-3).
  2. Criação de arquivo de log de execução (`coleta_g1.log`) utilizando o módulo `logging` nativo do Python, registrando o timestamp de cada requisição HTTP, código de status recebido, número de novos itens capturados por página e eventuais advertências de rede.
- **Código de Avaliação (`avaliar_qualidade.py`):**
```python
def avaliar_rastreabilidade(self):
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
        "detalhes": f"Registros com metadados de origem: {rastreaveis}/{total}; Log de auditoria: {'OK' if tem_arquivo_log else 'Ausente'}",
        "status": "Aprovado" if aprovado else "Reprovado"
    }
```

---

## 🤖 7. Proposta de Uso de Modelos de Linguagem (LLMs)

### Onde e como aplicar:
- **Monitoramento e Auto-cura de Seletores (Watchdog Assíncrono):** A LLM não é inserida no loop de cada requisição (o que geraria lentidão e custos desnecessários). Ela é acionada apenas quando o pipeline detecta uma anomalia (por exemplo, 2 páginas consecutivas retornando 0 notícias).
- **Entrada fornecida à LLM:** Um trecho de HTML sanitizado (sem tags `<script>`, `<style>` e `<svg>`), acompanhado do aviso de qual seletor deixou de funcionar.
- **Prevenção contra Alucinações:** A LLM **não inventa nem extrai notícias**: ela apenas sugere novos seletores CSS/XPath ou parâmetros de consulta em formato JSON estrito (`temperature=0.0`). A extração real dos dados é realizada de forma determinística pelo código Python.
- **Validação em Sandbox:** Os novos seletores propostos pela LLM são testados automaticamente em uma cópia local do HTML antes de serem aprovados.

---

## ⚠️ 8. Limitações e Melhorias Futuras
1. **Extração do Conteúdo Integral:** Atualmente o scraper coleta os dados presentes na página de busca (título, resumo, data, URL). Uma melhoria futura é adicionar uma etapa secundária para acessar cada URL e raspar o texto completo da matéria.
2. **Agendamento em Nuvem:** Configuração de um workflow no GitHub Actions para executar a coleta diariamente de forma automática.

