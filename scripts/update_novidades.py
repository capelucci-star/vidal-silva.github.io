import feedparser
import anthropic
import re
from datetime import datetime, timedelta
from pathlib import Path

# ── Config ──────────────────────────────────────────────────────────────────
BLOG_FEED = "https://avancosvidalcapelucci.blogspot.com/feeds/posts/default"
INDEX_FILE = Path("index.html")
MAX_ARTICLES = 5          # artigos mais recentes para o resumo

# ── 1. Buscar artigos da semana ──────────────────────────────────────────────
feed = feedparser.parse(BLOG_FEED)
cutoff = datetime.utcnow() - timedelta(days=7)

articles = []
for entry in feed.entries:
    pub = datetime(*entry.published_parsed[:6])
    if pub >= cutoff:
        # Remove HTML tags do resumo
        summary = re.sub(r"<[^>]+>", "", entry.get("summary", ""))[:600]
        articles.append({
            "title": entry.title,
            "link": entry.link,
            "summary": summary,
            "date": pub.strftime("%d/%m/%Y"),
        })

if not articles:
    print("Nenhum artigo novo esta semana. Nada a atualizar.")
    exit(0)

print(f"Encontrados {len(articles)} artigo(s) esta semana.")

# ── 2. Gerar resumo com Claude ───────────────────────────────────────────────
client = anthropic.Anthropic()   # usa ANTHROPIC_API_KEY do ambiente

articles_text = "\n\n".join(
    f"Título: {a['title']}\nData: {a['date']}\nLink: {a['link']}\nResumo: {a['summary']}"
    for a in articles[:MAX_ARTICLES]
)

prompt = f"""Você é o assistente editorial de Vidal Silva, Partner Sales Manager no Google Education.
Com base nos artigos abaixo publicados esta semana no blog "Avanços Vidal 2026", crie um bloco HTML
para a seção "Novidades" do seu site pessoal.

REGRAS:
- Tom: direto, visionário, autêntico — igual ao tom do site
- Máx 3 linhas de intro geral da semana
- Liste cada artigo como um item com: título linkado, data, e uma frase de 1 linha sobre o tema
- HTML limpo, sem estilos inline (use apenas as classes já existentes: recipe-card, section-title etc.)
- Retorne APENAS o bloco HTML, começando com <section> e terminando com </section>
- Use exatamente este marcador de abertura: <!-- NOVIDADES_START -->
- Use exatamente este marcador de fechamento: <!-- NOVIDADES_END -->

ARTIGOS DA SEMANA:
{articles_text}
"""

message = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=1024,
    messages=[{"role": "user", "content": prompt}]
)

html_block = message.content[0].text

# Remove crases de markdown caso o modelo as inclua
html_block = re.sub(r"```html\s*", "", html_block)
html_block = re.sub(r"```\s*", "", html_block)
html_block = html_block.strip()

print("Resumo gerado com sucesso.")

# ── 3. Atualizar index.html ──────────────────────────────────────────────────
content = INDEX_FILE.read_text(encoding="utf-8")

# Se já existe o bloco, substituir; senão, inserir antes do </main> ou </body>
if "<!-- NOVIDADES_START -->" in content:
    content = re.sub(
        r"<!-- NOVIDADES_START -->.*?<!-- NOVIDADES_END -->",
        html_block,
        content,
        flags=re.DOTALL,
    )
    print("Seção Novidades atualizada no index.html.")
else:
    # Insere antes do fechamento do body
    content = content.replace("</body>", f"\n{html_block}\n</body>")
    print("Seção Novidades inserida no index.html pela primeira vez.")

INDEX_FILE.write_text(content, encoding="utf-8")
print("index.html salvo com sucesso!")
