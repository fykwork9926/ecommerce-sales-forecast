# 📈 Previsão de Vendas no E-commerce

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)
![pandas](https://img.shields.io/badge/pandas-150458?logo=pandas&logoColor=white)
![NumPy](https://img.shields.io/badge/NumPy-013243?logo=numpy)
![Matplotlib](https://img.shields.io/badge/Matplotlib-gráficos-11557c)
![License](https://img.shields.io/badge/licença-MIT-green)
![Tests](https://github.com/SEU-USUARIO/ecommerce-sales-forecast/actions/workflows/tests.yml/badge.svg)

Projeto de análise de dados que usa o dataset real **Online Retail** (UCI) — cerca de **540 mil transações** de um varejista online do Reino Unido, com pedidos de 38 países entre dez/2010 e dez/2011 — para **limpar dados, detectar anomalias, segmentar clientes, categorizar produtos e prever as vendas das próximas semanas**.

> 💡 **Problema real:** um e-commerce precisa saber quanto vai vender para planejar estoque e caixa, quais clientes merecem atenção e quais produtos sustentam a receita. Este projeto responde às três perguntas a partir dos dados brutos de vendas.

![Previsão de vendas](docs/images/previsao.png)

---

## ✨ Funcionalidades

- 🧹 **Limpeza e detecção de anomalias** — identifica e trata:
  | Anomalia | Tratamento |
  |---|---|
  | Notas canceladas (começam com `C`) | Separadas e somadas no valor cancelado |
  | Quantidades negativas sem cancelamento | Removidas (ajustes de estoque) |
  | Preço zero ou negativo | Removidos (brindes e ajustes contábeis) |
  | Linhas duplicadas | Removidas |
  | Códigos que não são produto (`POST`, `M`, `DOT`...) | Removidos (frete, taxas) |
  | Vendas anuladas por um cancelamento posterior | Removidas (ex.: pedido de 80.995 unidades cancelado em seguida) |
  | Quantidades fora do padrão | Marcadas pela regra do IQR em escala log |
- 📅 **Séries temporais** — receita, pedidos e clientes por mês e por semana.
- 🌍 **Comparação entre países** — ticket médio e itens por pedido.
- 👥 **Segmentação de clientes (RFM)** — Recência, Frequência e Valor, com notas de 1 a 5 e seis segmentos (Campeões, Clientes fiéis, Em risco...).
- 🏷️ **Categorização de 3.700+ produtos** por três características:
  1. **Categoria temática** (palavras-chave na descrição)
  2. **Faixa de preço** (econômico, intermediário, premium)
  3. **Curva ABC** (participação na receita)
- 🔮 **Previsão de vendas** — quatro modelos implementados com NumPy competem em um **backtest** (as últimas semanas são escondidas e usadas como teste). O de menor erro (MAE) faz a previsão final, com intervalo aproximado de 95%.
- 📊 **Gráficos PNG** e **8 tabelas CSV** prontas para Excel/Power BI.

## 🛠️ Tecnologias utilizadas

- **Python 3.10+** — type hints, `dataclasses`, `pathlib`, `argparse`
- **pandas** — leitura, limpeza e agregações
- **NumPy** — modelos de previsão, métricas de erro e estatística
- **Matplotlib** — visualizações
- **unittest** + **GitHub Actions** — testes automatizados em Python 3.10, 3.11 e 3.12

## 🚀 Instalação e execução

### 1. Clone o repositório
```bash
git clone https://github.com/SEU-USUARIO/ecommerce-sales-forecast.git
cd ecommerce-sales-forecast
```

### 2. Crie e ative um ambiente virtual
```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux / macOS
source .venv/bin/activate
```

### 3. Instale as dependências
```bash
pip install -r requirements.txt
```

### 4. Baixe o dataset (~45 MB)
```bash
python -m salesforecast download
```
> Se o download falhar, baixe manualmente em [UCI – Online Retail](https://archive.ics.uci.edu/dataset/352/online+retail) e rode o passo 5 apontando para o arquivo (`.xlsx` exige `pip install openpyxl`).

### 5. Execute a análise
```bash
python -m salesforecast run
```

## 💻 Exemplos de uso

```bash
# Prever 12 semanas, usando 10 semanas no backtest
python -m salesforecast run --horizon 12 --test-weeks 10

# Usar outro arquivo e outra pasta de saída
python -m salesforecast run caminho/Online_Retail.xlsx -o resultados

# Só o relatório e os CSVs, sem gráficos
python -m salesforecast run --no-plots

# Ajuda completa
python -m salesforecast run --help
```

### Exemplo de saída no terminal

```text
$ python -m salesforecast run
Lendo data/online_retail.csv...
══════════════════════════════════════════════════════════════════
  SalesForecast — Análise e Previsão de Vendas
══════════════════════════════════════════════════════════════════

▶ QUALIDADE DOS DADOS E ANOMALIAS
  Linhas no arquivo .................. 541,909
  Linhas inválidas (data/número) ..... 0
  Linhas duplicadas .................. 5,268
  Cancelamentos (nota 'C...') ........ 9,251
  Valor cancelado (£) ................ £893,979.73
  Qtd. negativa sem cancelamento ..... 1,336
  Preço zero ou negativo ............. 1,176
  Códigos que não são produto ........ 2,374
  Vendas anuladas por cancelamento ... 3,083
  Vendas sem cliente identificado .... 131,354
  Quantidades fora do padrão ......... 10
  Linhas válidas após limpeza ........ 519,421

▶ VISÃO GERAL
  Período ............................ 2010-12 a 2011-12
  Receita total ...................... £9,852,281.73
  Produtos diferentes ................ 3,786
  Melhor mês ......................... 2011-11 (£1,441,098.47)

▶ TOP 5 PAÍSES POR TICKET MÉDIO (mín. 10 pedidos)
  País                    Pedidos   Ticket médio  Itens/pedido
  Netherlands                  93      £3,048.17         2,150
  Australia                    53      £2,586.09         1,574
  Japan                        19      £1,963.91         1,367
  Sweden                       32      £1,100.45         1,113
  Switzerland                  48      £1,098.18           631

▶ SEGMENTOS DE CLIENTES (RFM)
  Segmento                Clientes  % clientes  % receita
  Campeões                     971       22.5%      67.4%
  Clientes fiéis               838       19.4%      15.0%
  Em risco                     537       12.4%      10.0%
  Hibernando                 1,192       27.6%       4.6%
  Precisam de atenção          387        8.9%       1.6%
  Promissores                  397        9.2%       1.5%

▶ CATEGORIAS DE PRODUTOS
  Categoria               Produtos         Receita  % receita
  Cozinha e mesa               818   £3,074,754.19      31.2%
  Decoração                    626   £1,498,971.11      15.2%
  Natal e festas               287     £883,675.19       9.0%
  Casa e organização           183     £789,777.99       8.0%
  Iluminação                   278     £776,066.01       7.9%
  Bolsas                       153     £766,299.20       7.8%
  Outros                       535     £699,181.11       7.1%
  Papelaria                    305     £415,800.31       4.2%
  Brinquedos e jogos           117     £401,710.34       4.1%
  Joias e acessórios           374     £315,084.69       3.2%
  Jardim                       110     £230,961.59       2.3%
  Curva ABC: A=831 · B=964 · C=1991 produtos

▶ BACKTEST DOS MODELOS (últimas semanas escondidas)
  Modelo                                     MAE      MAPE
  Ingênuo (última semana)             £41,077.04     14.9% ◀ melhor
  Média móvel (4 semanas)             £48,973.02     15.9%
  Holt (suavização exponencial)       £74,373.89     27.4%
  Tendência linear                    £82,334.59     26.1%

▶ PREVISÃO — PRÓXIMAS 8 SEMANAS
  Semana de 05/12/2011     £308,193.68   (entre £209,272.34 e £407,115.02)
  Semana de 12/12/2011     £308,193.68   (entre £209,272.34 e £407,115.02)
  Semana de 19/12/2011     £308,193.68   (entre £209,272.34 e £407,115.02)
  Semana de 26/12/2011     £308,193.68   (entre £209,272.34 e £407,115.02)
  Semana de 02/01/2012     £308,193.68   (entre £209,272.34 e £407,115.02)
  Semana de 09/01/2012     £308,193.68   (entre £209,272.34 e £407,115.02)
  Semana de 16/01/2012     £308,193.68   (entre £209,272.34 e £407,115.02)
  Semana de 23/01/2012     £308,193.68   (entre £209,272.34 e £407,115.02)

══════════════════════════════════════════════════════════════════
```

## 📊 Visualizações

| Receita mensal | Ticket médio por país |
|---|---|
| ![Receita mensal](docs/images/receita_mensal.png) | ![Países](docs/images/ticket_medio_paises.png) |
| **Receita por segmento (RFM)** | **Receita por categoria** |
| ![Segmentos](docs/images/segmentos_rfm.png) | ![Categorias](docs/images/categorias.png) |

## 🔍 Principais descobertas

- **Sazonalidade forte de fim de ano:** novembro de 2011 foi o melhor mês, com cerca de £1,44 milhão — perto do dobro dos meses do primeiro semestre.
- **Concentração de receita:** os **Campeões** são ~22% dos clientes e geram ~67% da receita.
- **Atacado internacional:** Holanda e Austrália têm ticket médio acima de £2.500, muito maior que o do Reino Unido — típico de clientes revendedores.
- **Sobre a previsão:** no backtest, o modelo **ingênuo** (repetir a última semana) teve o menor erro (~15% de MAPE). Com só um ano de histórico não dá para aprender a sazonalidade anual, então modelos de tendência erram mais. A previsão é uma estimativa de curto prazo, e não captura a queda típica de janeiro.

## 🧪 Testes

```bash
python -m unittest discover -v
```

## 📁 Estrutura de arquivos

```text
ecommerce-sales-forecast/
├── .github/workflows/
│   └── tests.yml          # CI: roda os testes a cada push
├── data/                  # dataset baixado (ignorado pelo Git)
├── docs/images/           # gráficos usados neste README
├── reports/               # CSVs e gráficos gerados (ignorados pelo Git)
├── salesforecast/         # código-fonte do pacote
│   ├── __init__.py        # versão do projeto
│   ├── __main__.py        # permite rodar com "python -m salesforecast"
│   ├── cli.py             # comandos "download" e "run"
│   ├── config.py          # URL do dataset, colunas e constantes
│   ├── data_loader.py     # download e leitura (CSV/XLSX)
│   ├── cleaning.py        # limpeza e relatório de anomalias
│   ├── analysis.py        # séries temporais e comparação entre países
│   ├── segmentation.py    # segmentação RFM de clientes
│   ├── categorization.py  # categoria, faixa de preço e curva ABC
│   ├── forecasting.py     # modelos de previsão e backtest (NumPy)
│   ├── visualization.py   # gráficos (Matplotlib)
│   └── reporter.py        # relatório no terminal e exportação CSV
├── tests/                 # testes unitários (unittest)
├── .gitignore
├── LICENSE
├── README.md
└── requirements.txt
```

## 🗺️ Próximos passos

- [ ] Estimar lucro com uma margem configurável por categoria (o dataset tem só receita, não custo)
- [ ] Previsão diária com sazonalidade por dia da semana
- [ ] Modelos de séries temporais mais robustos (ex.: `statsmodels`, Prophet)
- [ ] Clusterização de clientes com K-Means (scikit-learn) para comparar com o RFM
- [ ] Dashboard interativo com Streamlit

## 📚 Dados

Dataset **Online Retail** — Daqing Chen, UCI Machine Learning Repository (2015). [DOI: 10.24432/C5BW33](https://doi.org/10.24432/C5BW33). Licença CC BY 4.0. Valores em libras esterlinas (£).

## 📝 Licença

Código distribuído sob a licença MIT. Veja [`LICENSE`](LICENSE).

---

Desenvolvido por **Fernando** · [LinkedIn](https://www.linkedin.com/in/SEU-PERFIL) · [GitHub](https://github.com/SEU-USUARIO)
