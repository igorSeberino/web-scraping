"""Gera o notebook da atividade (web_scraping_sentimentos.ipynb).

Mantido como script para que o notebook possa ser regenerado depois de ajustes.
"""
import nbformat as nbf

nb = nbf.v4.new_notebook()
c = []


def md(t):
    c.append(nbf.v4.new_markdown_cell(t.strip("\n")))


def code(t):
    c.append(nbf.v4.new_code_cell(t.strip("\n")))


md("""
# Raspagem de dados da Web + Análise de Sentimentos

**Disciplina:** T2ESOFT06NA · Ciência de Dados · 202623
**Loja escolhida:** [KaBuM!](https://www.kabum.com.br) · categoria *Headset Gamer*

Roteiro:
1. **Escolha do site** e verificação do `robots.txt` (T1)
2. **Raspagem** dos comentários com BeautifulSoup → `comentarios.csv` (T2)
3. **Rótulos e pré-processamento**: estrelas → Positivo/Negativo, stopwords, stemização RSLP (T3)
4. **Classificador Naive Bayes** (NLTK), acurácia e **matriz de confusão** (T4)
5. **Resultados e insights** (T5)
""")

code("""
import os, re, json, string, subprocess, urllib.robotparser
from collections import Counter

import requests
import pandas as pd
import matplotlib.pyplot as plt
from bs4 import BeautifulSoup

import nltk
nltk.download('stopwords', quiet=True)
nltk.download('rslp', quiet=True)
from nltk.corpus import stopwords
from nltk.stem import RSLPStemmer
from nltk import FreqDist, NaiveBayesClassifier
from nltk.classify import accuracy as nltk_accuracy
from sklearn.model_selection import train_test_split

SEMENTE = 42
pd.set_option('display.max_colwidth', 120)
""")

md("""
## 1. Escolha do site (T1)

Candidatos testados antes de escolher:

| Loja | Resultado |
|---|---|
| Buscapé (site do notebook de referência) | `robots.txt` bloqueia agentes de IA (`ClaudeBot`, `Claude-User`…) |
| Mercado Livre | idem |
| Magazine Luiza | 403 já no `robots.txt` |
| **KaBuM!** | `robots.txt` libera `/produto/` para `User-agent: *` → **escolhida** |

Abaixo, a verificação do `robots.txt` com `urllib.robotparser`, como o notebook de referência faz antes de coletar.
""")

code("""
ROBOTS = 'https://www.kabum.com.br/robots.txt'
try:
    linhas = requests.get(ROBOTS, timeout=15).text.splitlines()
    rp = urllib.robotparser.RobotFileParser()
    rp.parse(linhas)
    print('/produto/727786/ permitido para "*"?', rp.can_fetch('*', 'https://www.kabum.com.br/produto/727786/'))
    # o robotparser do Python não entende curingas (*), então confiro também as regras na mão
    disallow = [l.split(':', 1)[1].strip() for l in linhas if l.lower().startswith('disallow')]
    print('Regras Disallow que mencionam "produto":', [d for d in disallow if 'produto' in d] or 'nenhuma')
except Exception as e:
    print('Sem acesso ao robots.txt agora:', e)
""")

md("""
### Por que as páginas foram salvas do navegador (plano B)

A página de produto carrega os **comentários por JavaScript**, e a KaBuM **recusa requisições automatizadas**
(`requests` recebe HTTP 403). A célula abaixo mostra isso.

Por isso, seguindo o plano B (salvar a página com os comentários visíveis e raspar o arquivo salvo, como o notebook
de referência faz com páginas baixadas), cada produto foi aberto num navegador comum. As páginas de avaliações
foram percorridas com pausa de ~1 s entre elas, e o HTML de cada `<article>` de avaliação foi salvo (sem ícones e
imagens) em `dados/paginas/kabum_<id>.html`. Para garantir comentários negativos, além de "Todas as notas"
foram usados os filtros de 1 e 2 estrelas do próprio site.
""")

code("""
try:
    r = requests.get('https://www.kabum.com.br/produto/727786/', timeout=15)
    print('HTTP', r.status_code, '| tem dados de avaliação no HTML?', 'aggregateRating' in r.text)
except Exception as e:
    print('Erro de rede:', e)
""")

md("""
### Arquivos salvos

No Colab, a célula abaixo baixa os arquivos do repositório do trabalho (se a pasta `dados/` ainda não existir).
""")

code("""
REPO = 'https://github.com/igorSeberino/web-scraping.git'
PASTA = 'dados/paginas'
if not os.path.isdir(PASTA):
    subprocess.run(['git', 'clone', '--depth', '1', REPO, 'web-scraping'], check=False)
    PASTA = 'web-scraping/dados/paginas'
arquivos = sorted(f for f in os.listdir(PASTA) if f.endswith('.html'))
arquivos
""")

md("""
Estrutura de uma avaliação no HTML salvo (inspecionada no navegador, como no notebook de referência):

```html
<article>
  <span>Autor</span>
  <span class="sr-only">Nota 5 de 5</span>
  <span>Avaliado em 07/06/2026</span>
  <h3>Título</h3>
  <p>Texto do comentário</p>
</article>
```
""")

code("""
# T1: uma página raspada com BeautifulSoup
with open(os.path.join(PASTA, 'kabum_727786.html'), encoding='utf-8') as f:
    sopa = BeautifulSoup(f.read(), 'html.parser')

print('Produto:', sopa.find('h1').get_text(strip=True))
primeira = sopa.find('article')
print('Nota   :', primeira.find('span', class_='sr-only').get_text(strip=True))
print('Título :', primeira.find('h3').get_text(strip=True) if primeira.find('h3') else '')
print('Texto  :', primeira.find('p').get_text(strip=True) if primeira.find('p') else '')
""")

md("## 2. Raspagem dos comentários (T2)")

code("""
def raspar_arquivo(caminho):
    with open(caminho, encoding='utf-8') as f:
        sopa = BeautifulSoup(f.read(), 'html.parser')
    produto = sopa.find('h1').get_text(strip=True)
    linhas = []
    for art in sopa.find_all('article'):
        spans = art.find_all('span', recursive=False)
        nota_txt = art.find('span', class_='sr-only').get_text(strip=True)    # "Nota 4 de 5"
        titulo = art.find('h3').get_text(' ', strip=True) if art.find('h3') else ''
        texto = art.find('p').get_text(' ', strip=True) if art.find('p') else ''
        data = next((s.get_text(strip=True) for s in spans if s.get_text().startswith('Avaliado em')), '')
        linhas.append({
            'produto': produto,
            'nota': int(re.search(r'Nota (\\d)', nota_txt).group(1)),
            'comentario': (titulo + '. ' + texto).strip('. ') if texto else titulo,
            'autor': spans[0].get_text(strip=True) if spans else '',
            'data': data.replace('Avaliado em', '').strip(),
        })
    return linhas

registros = []
for arq in arquivos:
    registros += raspar_arquivo(os.path.join(PASTA, arq))

df_bruto = pd.DataFrame(registros)
print('Avaliações lidas (com repetidas):', len(df_bruto))
df_bruto.head()
""")

md("""
Limpeza: a mesma avaliação pode aparecer em "Todas as notas" e no filtro de 1 ou 2 estrelas, por isso removo as
repetidas (mesmo produto, autor, data, nota e texto). Também removo comentários vazios.
""")

code("""
df = df_bruto.copy()
df['comentario'] = df['comentario'].str.replace(r'\\s+', ' ', regex=True).str.strip()
df = df[df['comentario'] != '']
df = df.drop_duplicates(subset=['produto', 'autor', 'data', 'nota', 'comentario'])
df = df[['produto', 'nota', 'comentario']].drop_duplicates().reset_index(drop=True)

# nomes curtos para os gráficos
nome = df['produto'].str.replace('Headset Gamer ', '', regex=False).str.split(',').str[0].str.slice(0, 30)
modelo = df['produto'].str.rsplit(' - ', n=1).str[-1]
df['produto_curto'] = nome + ' (' + modelo + ')'

print('Avaliações após limpeza:', len(df))
print('Comentários vazios     :', df.comentario.str.strip().eq('').sum())
print('Linhas duplicadas      :', df.duplicated().sum())
# acento quebrado = UTF-8 lido como latin1 ("Ã§" no lugar de "ç"); "NÃO" em maiúsculas é legítimo
MOJIBAKE = r'Ã[\\x80-\\xbf]|Ã§|Ã£|Ã©|Ã¡|Ãª|Ã³|Ãº|Ã\\xad'
print('Acento quebrado ("Ã§"…):', df.comentario.str.contains(MOJIBAKE, regex=True).sum())
print('  ("Ã" legítimo, ex. NÃO:', df.comentario.str.contains('Ã').sum(), 'linhas)')
df.nota.value_counts().sort_index()
""")

code("""
df[['produto', 'nota', 'comentario']].to_csv('comentarios.csv', index=False, encoding='utf-8')
volta = pd.read_csv('comentarios.csv')
print('Linhas gravadas:', len(df), '| linhas lidas de volta:', len(volta))
df.groupby('produto_curto').nota.agg(['count', 'mean']).round(2).sort_values('count', ascending=False)
""")

md("""
## 3. Rótulos e pré-processamento (T3)

Rótulo pelas estrelas (D3): **4–5 = Positivo**, **1–2 = Negativo**. Nota **3** fica fora do treino e só recebe
previsão no final.

Pré-processamento do material de referência: minúsculas, remoção de pontuação e de *stopwords* em português,
stemização **RSLP**.
""")

code("""
def rotular(nota):
    if nota >= 4: return 'Positivo'
    if nota <= 2: return 'Negativo'
    return None

df['sentimento'] = df['nota'].apply(rotular)

PALAVRAS_DE_NEGACAO = {'não', 'nem', 'nunca', 'sem', 'mas', 'porém'}
STOP = set(stopwords.words('portuguese')) - PALAVRAS_DE_NEGACAO   # mantém negações: "não funciona" ≠ "funciona"
stemmer = RSLPStemmer()
TABELA = str.maketrans({p: ' ' for p in string.punctuation + '“”‘’…–—'})

def tokens_limpos(texto):
    texto = texto.lower().translate(TABELA)
    return [t for t in texto.split() if t not in STOP and not t.isdigit() and len(t) > 1]

def preprocessar(texto):
    return [stemmer.stem(t) for t in tokens_limpos(texto)]

df['tokens'] = df['comentario'].apply(tokens_limpos)
df['stems'] = df['comentario'].apply(preprocessar)

rotulados = df[df['sentimento'].notna()].copy()
print(rotulados['sentimento'].value_counts())
print('Notas no conjunto de treino/teste:', sorted(rotulados.nota.unique()))
""")

code("""
exemplos = pd.concat([rotulados[rotulados.sentimento == 'Negativo'].head(2), rotulados[rotulados.sentimento == 'Positivo'].head(1)])
for _, l in exemplos.iterrows():
    print(f"[{l.sentimento}] ANTES : {l.comentario[:150]}")
    print(f"{' ' * (len(l.sentimento) + 2)} DEPOIS: {l.stems[:20]}\\n")
""")

md("""
## 4. Classificador Naive Bayes (T4)

Atributos: presença de cada radical (*bag of words*) dentre os 2.000 mais frequentes, como no material de referência.
Divisão **80/20 estratificada** pelo rótulo, semente 42.
""")

code("""
todas_stems = FreqDist(s for lista in rotulados['stems'] for s in lista)
VOCAB = [w for w, _ in todas_stems.most_common(2000)]

def atributos(stems):
    presentes = set(stems)
    return {f'tem({w})': (w in presentes) for w in VOCAB}

treino, teste = train_test_split(rotulados, test_size=0.2, stratify=rotulados['sentimento'], random_state=SEMENTE)
conj_treino = [(atributos(s), y) for s, y in zip(treino['stems'], treino['sentimento'])]
conj_teste = [(atributos(s), y) for s, y in zip(teste['stems'], teste['sentimento'])]

classificador = NaiveBayesClassifier.train(conj_treino)
print(f'Treino: {len(treino)} | Teste: {len(teste)}')
print(f'Acurácia no teste: {nltk_accuracy(classificador, conj_teste):.3f}')
""")

code("""
y_real = [y for _, y in conj_teste]
y_prev = [classificador.classify(x) for x, _ in conj_teste]
rot = ['Positivo', 'Negativo']
matriz = pd.crosstab(pd.Series(y_real, name='Real'), pd.Series(y_prev, name='Previsto')).reindex(index=rot, columns=rot, fill_value=0)
print(matriz, '\\n')

for classe in rot:
    vp = matriz.loc[classe, classe]
    prec = vp / matriz[classe].sum() if matriz[classe].sum() else 0
    rec = vp / matriz.loc[classe].sum() if matriz.loc[classe].sum() else 0
    print(f'{classe:9s} precisão={prec:.2f}  revocação={rec:.2f}')

fig, ax = plt.subplots(figsize=(4, 3.5))
ax.imshow(matriz.values, cmap='Blues')
for i in range(2):
    for j in range(2):
        ax.text(j, i, matriz.values[i, j], ha='center', va='center', fontsize=14,
                color='white' if matriz.values[i, j] > matriz.values.max() / 2 else 'black')
ax.set_xticks([0, 1], rot); ax.set_yticks([0, 1], rot)
ax.set_xlabel('Previsto'); ax.set_ylabel('Real'); ax.set_title('Matriz de confusão (teste)')
plt.tight_layout(); plt.show()
""")

code("""
classificador.show_most_informative_features(10)
""")

code("""
df['sentimento_previsto'] = [classificador.classify(atributos(s)) for s in df['stems']]
print('Previsões vazias:', df['sentimento_previsto'].isna().sum())
print('\\nComentários de nota 3 (fora do treino) e o sentimento previsto:')
df[df.nota == 3][['produto_curto', 'comentario', 'sentimento_previsto']]
""")

md("## 5. Resultados e insights (T5)")

code("""
prop = (df.groupby('produto_curto')['sentimento_previsto'].value_counts(normalize=True)
          .unstack(fill_value=0).reindex(columns=['Positivo', 'Negativo'], fill_value=0)
          .sort_values('Negativo'))
ax = prop.plot(kind='barh', stacked=True, color=['#2b8a3e', '#c92a2a'], figsize=(8, 4.5))
ax.set_xlabel('Proporção dos comentários (sentimento previsto)'); ax.set_ylabel('')
ax.set_title('Positivo × Negativo por produto'); ax.legend(loc='lower right')
ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f'{v:.0%}'))
plt.tight_layout(); plt.show()
(prop * 100).round(1)
""")

md("""
Atenção: a proporção de negativos aqui **não** é a proporção real da loja, porque a coleta usou os filtros de
1 e 2 estrelas para ter exemplos negativos suficientes (ver Limitações). Ela serve para comparar produtos entre si.
""")

code("""
fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
top = {}
for ax, classe, cor in zip(axes, ['Positivo', 'Negativo'], ['#2b8a3e', '#c92a2a']):
    fd = FreqDist(t for lista in rotulados[rotulados.sentimento == classe]['tokens'] for t in lista)
    top[classe] = fd.most_common(15)
    palavras, freq = zip(*top[classe])
    ax.barh(palavras[::-1], freq[::-1], color=cor)
    ax.set_title(f'15 palavras mais frequentes · {classe}')
plt.tight_layout(); plt.show()
pd.DataFrame({k: [f'{w} ({n})' for w, n in v] for k, v in top.items()})
""")

code("""
# Assuntos que mais aparecem nos comentários negativos
neg = rotulados[rotulados.sentimento == 'Negativo']
temas = {
    'microfone': r'micro|mic\\b', 'som / áudio': r'\\bsom\\b|áudio|audio|chiado|chiand',
    'defeito / parou': r'defeit|parou|quebr|estrag|não funcion|nao funcion',
    'conexão / bateria': r'bateria|bluetooth|conex|desconect|carreg|sem fio|wireless',
    'conforto / tamanho': r'confort|apert|dói|doi\\b|orelha|cabeça',
    'entrega / atendimento': r'entreg|troca|devolu|suporte|atendimento|garantia',
}
contagem = {t: neg['comentario'].str.lower().str.contains(p, regex=True).mean() for t, p in temas.items()}
(pd.Series(contagem).sort_values(ascending=False) * 100).round(1).rename('% dos comentários negativos')
""")

md("""
### Insights

Os números citam as células de código pela ordem de execução ("Reiniciar e executar tudo").

1. **O classificador acerta 86,2% no teste, com erros equilibrados** (células [11] e [12]). Dos 37 positivos, 32 foram
   acertados; dos 28 negativos, 24. Precisão e revocação ficam entre 0,83 e 0,89 nas duas classes, então o modelo não
   está só "chutando Positivo", o que é o risco com classes desbalanceadas.
2. **O microfone é a principal reclamação.** Aparece em **56,9%** dos comentários negativos (célula [17]) e é a 2ª
   palavra mais frequente da classe Negativo (134 ocorrências, contra 27 nos positivos, célula [16]).
3. **Durabilidade pesa mais que qualidade inicial.** 44,5% dos negativos falam de defeito ou de algo que "parou"
   (célula [17]). As palavras mais informativas do modelo são quase todas desse tema: `func`/`funcion` (16,6 : 1),
   `problem`, `par` (parou), `dur` (durou), `defeit` (célula [13]). Muitos negativos elogiam o som e reclamam que o
   produto quebrou meses depois.
4. **Os positivos falam de custo-benefício e som:** `bom`, `qualidade`, `som`, `excelente`, `preço` estão no top 15
   (célula [16]). "Bom" é tão comum que aparece também entre os negativos ("é bom, mas…"); por isso `porém` virou um
   forte indicador de Negativo (12,1 : 1, célula [13]).
5. **Comentários mistos enganam o modelo.** Das 6 avaliações de nota 3, 5 foram previstas como Positivo (célula [14]),
   inclusive "Áudio extremamente baixo…" e "Bonito porém de qualidade fraca". O modelo aprendeu bem os extremos (1–2 e
   4–5), mas tende a Positivo quando o texto mistura elogio e crítica.
6. **Entre os produtos** (célula [15]), o HP H320 tem a maior proporção positiva (94%), e o Havit HV-H2002D a menor
   (57% negativos). Mas o Havit tem média **4,8 no site** com 3.476 avaliações, contra 2,52 na nossa base (célula [8]):
   a diferença vem da coleta, que priorizou os filtros de 1 e 2 estrelas nesse produto. É um bom exemplo de como o
   modo de amostragem muda a conclusão.
""")

md("""
### Limitações

- **Classes desbalanceadas e amostra enviesada.** Na loja, a grande maioria das avaliações é 4–5 estrelas. Para ter
  negativos suficientes, a coleta usou os filtros de 1 e 2 estrelas, então a proporção de negativos na base é bem maior
  que a real. A acurácia também precisa ser lida junto com a matriz de confusão, e não sozinha.
- **Estrela ≠ texto.** O rótulo vem da nota, não do texto. Há comentários de 5 estrelas que reclamam de algo e de
  1 estrela que elogiam o produto mas reclamam da entrega. O classificador aprende com esses rótulos "ruidosos".
- **Base pequena.** Com algumas centenas de comentários curtos, poucas palavras decidem a previsão. Uma palavra
  rara pode pesar demais (veja as palavras mais informativas).
- **Uma categoria só.** Todos os produtos são headsets, então as conclusões não valem para outras categorias.
- **Coleta pelo navegador.** O site bloqueia `requests` (HTTP 403). As páginas foram salvas do navegador e raspadas
  localmente; refazer a coleta exige repetir esse passo.
""")

nb["cells"] = c
nb["metadata"]["kernelspec"] = {"name": "python3", "display_name": "Python 3", "language": "python"}
nb["metadata"]["language_info"] = {"name": "python"}
nbf.write(nb, "web_scraping_sentimentos.ipynb")
print("ok", len(c), "células")
