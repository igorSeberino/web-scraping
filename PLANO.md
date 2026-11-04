# Raspagem de dados da Web + Análise de Sentimentos · Plano

Tamanho: pequeno (1 entrega, 1 pessoa). Nível: plano (tarefas com aceite e dependências).
Disciplina: T2ESOFT06NA | CIÊNCIA DE DADOS | 202623.

## 1. Fontes

| Fonte | O que fixa |
|---|---|
| Enunciado no Teams (capturas de tela da atividade) | R1–R4, prazo, envios múltiplos |
| `Analise-de-Sentimentos.pdf` (material de referência, 22 p.) | R5 e a técnica do D5 |
| `DS-data-scraping-com-beautifulsoup.ipynb` (material de referência, aula de 2017 sobre o BuscaPé) | o método de raspagem dos D2 e D6 e os cuidados de T1 e T2 |

## 2. Requisitos

| R | Trecho literal (local) | Onde é atendido |
|---|---|---|
| R1 | "Escolher um site e-Commerce para fazer Web Scraping de produtos (escolha livre)." (Teams, Instruções) | T1, T2 |
| R2 | "Aplicar Análise de Sentimentos para identificar nos comentários dos produtos o sentimento (Positivo / Negativo)." (Teams, Instruções) | T3, T4 |
| R3 | "Apresentar resultados/insights." (Teams, Instruções) | T5 |
| R4 | "Vence hoje às 22:30 • Vários envios permitidos" (Teams, cabeçalho) | T6, D8 |
| R5 | "a necessidade de sempre analisar a eficácia do algoritmo para evitar análises erradas, para o qual devemos fazer uso da matriz de confusão." (PDF p.18–19) | T4 |

Não é requisito: "Ver Anexos." (Teams) é indicação de leitura; vira D5 e D6, não R.
"Pontos: Sem pontos" (Teams) não fixa nada a construir.
Os "Exercícios" do notebook (célula 37) são da aula sobre preços de iPhone no BuscaPé, não desta atividade.

## 3. Decisões

| D | Decisão | Quem | Motivo | Descartado |
|---|---|---|---|---|
| D1 | Trabalho individual | usuário | — | grupo |
| D2 | Site escolhido em T1 por teste: fica o primeiro candidato cujo HTML (sem JavaScript) traz texto do comentário **e** nota em estrelas. Plano B: salvar a página do produto no navegador com os comentários visíveis e raspar o arquivo salvo, como o notebook faz com páginas baixadas (células 3, 23–26) | usuário pediu para o agente decidir | não deu para testar sites a partir do ambiente do agente; a escolha é livre (R1) | fixar um site sem teste |
| D3 | Rótulo pelas estrelas: 4–5 = Positivo, 1–2 = Negativo, 3 fica fora do treino | usuário | rótulo vem do próprio site e permite treino/teste e matriz de confusão (R5) | rotular à mão; léxico |
| D4 | Entrega = um notebook `.ipynb` no Google Colab, com os insights numa seção final em Markdown | usuário | o PDF (p.2) sugere Colab; o anexo de referência é `.ipynb` | notebook + slides |
| D5 | Pipeline do PDF: minúsculas, remoção de stopwords em português e pontuação (p.6–7), stemização RSLP (p.7), `FreqDist` (p.8), Naive Bayes do NLTK (p.10), acurácia e matriz de confusão (p.14–18) | agente | é a técnica do material de referência | modelos pré-treinados (BERT, léxicos prontos) |
| D6 | Raspagem com `requests` + BeautifulSoup + pandas, no estilo do notebook: inspecionar a tag e a classe no HTML, `find`/`find_all`, uma lista de dicionários virando `DataFrame` e depois `to_csv` (células 1, 14–17, 35–36) | agente | é o método do anexo de referência | Selenium/navegador automatizado |
| D7 | Volume alvo: ≥ 200 comentários com nota, e ≥ 30 em cada classe após D3. Se Negativo < 30, incluir produtos com nota média mais baixa | agente (**hipótese**: limiar sem fonte, só para o teste ter as duas classes) | Naive Bayes e matriz de confusão precisam das duas classes no teste | sem limiar |
| D8 | Primeiro envio no Teams assim que T4 passar; reenviar depois de T5 | agente | R4 permite vários envios; protege contra perder o prazo | enviar só no fim |
| D9 | Treino/teste 80/20 estratificado pelo rótulo, semente 42 | agente | resultado reproduzível ao rodar de novo | sem semente |

## 4. Fora do escopo

- Classe Neutro — o enunciado pede só Positivo / Negativo (R2).
- Seis emoções (alegria, medo…) do PDF p.3 — o enunciado pede só polaridade.
- Clusterização (PDF p.5) — exemplo do texto, não pedido.
- Selenium ou navegador automatizado — D6; o plano B do D2 cobre site com JavaScript.
- Slides, dashboard, deploy, API — D4.
- README, LICENSE, `requirements.txt` — a entrega é o notebook no Teams.
- Issues e Project no GitHub — não pedidos.
- Rotulagem manual e comparação entre vários modelos — D3 e D5.

## 5. Tarefas

Grafo: `T1 → T2 → T3 → T4 → {T5, T6}`; T6 é reenviada depois de T5 (D8).

| T | Entrega | Atende | Bloqueada por |
|---|---|---|---|
| T1 | Site escolhido e uma página de produto raspada | R1, D2, D6 | — |
| T2 | Base `comentarios.csv` com `produto, nota, comentario` | R1, D7 | T1 |
| T3 | Rótulos e texto pré-processado | R2, D3, D5 | T2 |
| T4 | Classificador treinado e avaliado | R2, R5, D5, D9 | T3 |
| T5 | Resultados e insights no notebook | R3, D4 | T4 |
| T6 | Notebook entregue no Teams | R4, D4, D8 | T4 (1º envio), T5 (reenvio) |

### T1 · Escolher o site
Testar 2–3 lojas candidatas na ordem que preferir. Para cada uma: abrir `/robots.txt` (o notebook
deixa de coletar um caminho que o `robots.txt` proíbe, célula 27), baixar uma página de produto com `requests` e procurar no HTML um trecho de comentário que você vê na tela.
Nenhuma passou → plano B do D2.
- [ ] Célula imprime ≥ 1 comentário com texto e nota extraídos por BeautifulSoup da página do site escolhido.
- [ ] O caminho usado não aparece em `Disallow` do `robots.txt` do site.

### T2 · Raspar os comentários
Percorrer produtos (e páginas de comentários, se houver) com pausa ≥ 1 s entre requisições. Para testar o
parser sem acessar o site de novo a cada vez, salvar as páginas uma vez e parsear os arquivos locais (notebook, células 2 e 23).
Se os acentos saírem quebrados, ajustar a codificação (notebook, células 2–5: `latin1` × UTF-8).
- [ ] `len(df) >= 200` (D7) e `df.comentario.str.strip().eq('').sum() == 0`.
- [ ] `df.duplicated().sum() == 0` depois da limpeza.
- [ ] `df.comentario.str.contains('Ã').sum() == 0` (não há acento quebrado, como "Ã§" no lugar de "ç").
- [ ] `df.to_csv('comentarios.csv')` roda e o arquivo é lido de volta com o mesmo número de linhas.

### T3 · Rotular e pré-processar
- [ ] Coluna `sentimento` só com `Positivo`/`Negativo`; nenhuma linha de treino com nota 3 (D3).
- [ ] `value_counts()` de `sentimento` mostra ≥ 30 em cada classe (D7).
- [ ] Célula mostra 3 comentários antes e depois de stopwords + stemização.

### T4 · Treinar e avaliar
- [ ] Acurácia no conjunto de teste impressa (D9).
- [ ] Matriz de confusão 2×2 Positivo/Negativo impressa (R5).
- [ ] Lista das 10 palavras mais informativas do classificador impressa.
- [ ] Coluna `sentimento_previsto` preenchida para todos os comentários, inclusive os de nota 3.

### T5 · Resultados e insights
- [ ] Gráfico da proporção Positivo/Negativo por produto.
- [ ] 15 palavras mais frequentes de cada classe (`FreqDist`, PDF p.8).
- [ ] Seção Markdown "Insights" com ≥ 3 conclusões, cada uma citando um número de célula acima.
- [ ] Seção "Limitações": desbalanceamento das classes e "estrela ≠ texto" (D3).

### T6 · Entregar
- [ ] Colab: "Ambiente de execução → Reiniciar e executar tudo" termina sem erro.
- [ ] `.ipynb` anexado em "Meu trabalho → Anexo" e botão "Entregar" clicado antes das 22:30.

## 6. Pronto
- [ ] Toda caixa de T1–T6 marcada.
- [ ] O Teams mostra a atividade como entregue.
