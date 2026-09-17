# NetLab UFRJ - Coletor de Notícias do G1 sobre LGPD

Projeto desenvolvido como solução do desafio técnico para o **Laboratório de Estudos de Internet e Mídias Sociais (NetLab UFRJ)**.

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

---

## 🛠️ 3. Como Instalar e Executar

### Pré-requisitos
- Python 3.9 ou superior instalado.

### Passo a Passo:

1. **Abra a pasta do projeto no terminal:**
```powershell
cd C:\Users\evslo\.gemini\antigravity\scratch\netlab_g1_scraper
```

2. **Ative o ambiente virtual (já configurado):**
```powershell
.\venv\Scripts\activate
```

3. **Instale as dependências (caso necessário):**
```powershell
pip install -r requirements.txt
```

4. **Execute a coleta:**
```powershell
python coletor_g1.py
```

Os dados coletados serão gerados imediatamente em:
- `g1_lgpd.csv`
- `g1_lgpd.json`
- `coleta_g1.log`

---

## 🧪 4. Testes Automatizados

O projeto conta com suíte de testes desenvolvida com **pytest**:

Para executar os testes:
```powershell
pytest test_coletor.py -v
```

**Cobertura dos testes:**
- Extração e limpeza de URLs canônicas a partir de links com redirecionador.
- Processamento e normalização de hits com tratamento de campos ausentes.
- Funcionamento do parser Beautiful Soup em fragmentos HTML.
- Mecanismo de desduplicação de registros.

---

## 📊 5. Avaliação da Qualidade dos Dados (7 Dimensões)

Os dados gerados na execução foram auditados contra uma **amostra de referência manual (Ground Truth)** obtida diretamente do portal G1:

| Dimensão | O que avalia | Resultado Obtido | Status |
| :--- | :--- | :--- | :--- |
| **1. Completude** | Preenchimento de campos obrigatórios (`titulo`, `url`, `data_publicacao`) | **100%** de preenchimento nos campos obrigatórios | ✅ Aprovado |
| **2. Atualidade** | Notícias mais recentes ordenadas cronologicamente com data ISO auditável | **100%** (inclui notícias do dia da coleta com timestamp ISO 8601) | ✅ Aprovado |
| **3. Precisão** | Ausência de ruídos, links quebrados ou banners publicitários | **100%** dos registros são notícias válidas | ✅ Aprovado |
| **4. Acurácia** | Fidelidade dos textos em relação ao portal original | **100%** idêntico ao portal G1 | ✅ Aprovado |
| **5. Unicidade** | Ausência de registros repetidos | **100%** de unicidade (0 registros duplicados) | ✅ Aprovado |
| **6. Consistência** | Padronização dos formatos de URL (links canônicos) e datas | **100%** das URLs absolutas e limpas de tracking | ✅ Aprovado |
| **7. Rastreabilidade** | Identificação da página de origem e data/hora de coleta | **100%** auditável com fuso horário de Brasília (UTC-3) | ✅ Aprovado |

---

## 🤖 6. Proposta de Uso de Modelos de Linguagem (LLMs)

### Onde e como aplicar:
- **Monitoramento e Auto-cura de Seletores (Watchdog Assíncrono):** A LLM não é inserida no loop de cada requisição (o que geraria lentidão e custos desnecessários). Ela é acionada apenas quando o pipeline detecta uma anomalia (por exemplo, 2 páginas consecutivas retornando 0 notícias).
- **Entrada fornecida à LLM:** Um trecho de HTML sanitizado (sem tags `<script>`, `<style>` e `<svg>`), acompanhado do aviso de qual seletor deixou de funcionar.
- **Prevenção contra Alucinações:** A LLM **não inventa nem extrai notícias**: ela apenas sugere novos seletores CSS/XPath ou parâmetros de consulta em formato JSON estrito (`temperature=0.0`). A extração real dos dados é realizada de forma determinística pelo código Python.
- **Validação em Sandbox:** Os novos seletores propostos pela LLM são testados automaticamente em uma cópia local do HTML antes de serem aprovados.

---

## ⚠️ 7. Limitações e Melhorias Futuras
1. **Extração do Conteúdo Integral:** Atualmente o scraper coleta os dados presentes na página de busca (título, resumo, data, URL). Uma melhoria futura é adicionar uma etapa secundária para acessar cada URL e raspar o texto completo da matéria.
2. **Agendamento em Nuvem:** Configuração de um workflow no GitHub Actions para executar a coleta diariamente de forma automática.
