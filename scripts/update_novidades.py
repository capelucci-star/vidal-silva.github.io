import feedparser
import anthropic
import re
from datetime import datetime, timedelta
from pathlib import Path

# ── Config ───────────────────────────────────────────────────────────────────
BLOG_FEED = "https://avancosvidalcapelucci.blogspot.com/feeds/posts/default"
INDEX_FILE = Path("index.html")
MAX_ARTICLES = 3  # máximo de artigos no card

# ── 1. Buscar artigos da semana ───────────────────────────────────────────────
feed = feedparser.parse(BLOG_FEED)
cutoff = datetime.utcnow() - timedelta(days=7)

articles = []
for entry in feed.entries:
    pub = datetime(*entry.published_parsed[:6])
    if pub >= cutoff:
        summary = re.sub(r"<[^>]+>", "", entry.get("summary", ""))[:300]
        articles.append({
            "title": entry.title,
            "link": entry.link,
            "date": pub.strftime("%d/%m/%Y"),
            "summary": summary,
        })

if not articles:
    print("Nenhum artigo novo esta semana. Nada a atualizar.")
    exit(0)

print(f"Encontrados {len(articles)} artigo(s) esta semana.")

# ── 2. Gerar itens da lista com Claude ───────────────────────────────────────
client = anthropic.Anthropic()

articles_text = "\n\n".join(
    f"Título: {a['title']}\nData: {a['date']}\nLink: {a['link']}"
    for a in articles[:MAX_ARTICLES]
)

prompt = f"""Gere APENAS os itens <li> para uma lista HTML de artigos de blog.

FORMATO EXATO para cada artigo:
<li>
  <a href="URL" target="_blank">TÍTULO</a>
  <span>DATA</span>
</li>

NÃO inclua nenhuma outra tag, texto, explicação ou marcador de código. Apenas os <li>.

ARTIGOS:
{articles_text}"""

message = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=512,
    messages=[{"role": "user", "content": prompt}]
)

li_items = message.content[0].text
li_items = re.sub(r"```html\s*", "", li_items)
li_items = re.sub(r"```\s*", "", li_items)
li_items = li_items.strip()

print("Itens gerados com sucesso.")

# ── 3. Montar o card completo ─────────────────────────────────────────────────
card_html = """<!-- NOVIDADES_START -->
        <div class="card card-novidades">
            <i class="fas fa-newspaper"></i>
            <h3>Novidades da Semana</h3>
            <p>Resumo dos artigos publicados esta semana no blog — atualizado toda sexta-feira.</p>
            <ul class="novidades-list">
                {li_items}
            </ul>
            <a href="https://avancosvidalcapelucci.blogspot.com/" target="_blank" style="color: var(--primary); text-decoration: none; font-weight: bold; margin-top:15px;">Ver todos os artigos →</a>
        </div>
        <!-- NOVIDADES_END -->""".format(li_items=li_items)

# ── 4. Atualizar index.html ───────────────────────────────────────────────────
content = INDEX_FILE.read_text(encoding="utf-8")

if "<!-- NOVIDADES_START -->" in content:
    content = re.sub(
        r"<!-- NOVIDADES_START -->.*?<!-- NOVIDADES_END -->",
        card_html,
        content,
        flags=re.DOTALL,
    )
    print("Card de Novidades atualizado no index.html.")
else:
    print("ERRO: Marcador <!-- NOVIDADES_START --> não encontrado no index.html.")
    exit(1)

INDEX_FILE.write_text(content, encoding="utf-8")
print("index.html salvo com sucesso!")
