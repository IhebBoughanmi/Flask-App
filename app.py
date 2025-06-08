!pip install newspaper3k deep-translator
!pip install lxml[html_clean]

from newspaper import Article
from deep_translator import GoogleTranslator
from html import escape

def extraire_et_traduire_en_html(
    url,
    langue_source='auto',
    langue_cible='ar',
    nom_fichier_html="traduction_article.html"
):

    article = Article(url)
    article.download()
    article.parse()

    titre_original = article.title.strip()
    texte_original = article.text.strip()
    paragraphes = [p.strip() for p in texte_original.split('\n') if p.strip()]

    html = f"""<!DOCTYPE html>
<html lang="{langue_cible}">
<head>
    <meta charset="UTF-8">
    <title>Traduction de l'article</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, sans-serif;
            line-height: 1.6;
            direction: rtl;
            background-color: #f9f9f9;
            color: #333;
            padding: 40px;
        }}
        h1 {{
            text-align: center;
            color: #222;
        }}
        p {{
            margin-bottom: 20px;
        }}
        .original {{
            font-size: 0.9em;
            color: #555;
            font-style: italic;
        }}
    </style>
</head>
<body>
    <h1>{escape(titre_original)}</h1>
"""

    for i, p in enumerate(paragraphes):
        try:
            traduction = GoogleTranslator(source=langue_source, target=langue_cible).translate(p)
            html += f"<p>{escape(traduction)}</p>\n"
        except Exception as e:
            print(f"Erreur à la traduction du paragraphe {i+1} : {e}")
            html += f'<p class="original">[NON TRADUIT] {escape(p)}</p>\n'

    html += """
</body>
</html>
"""

    with open(nom_fichier_html, 'w', encoding='utf-8') as fichier:
        fichier.write(html)

    print(f" Fichier HTML généré : {nom_fichier_html}")


url_article = "https://www.weforum.org/stories/2025/03/ai-healthcare-strategy-speed/"
extraire_et_traduire_en_html(url_article, nom_fichier_html="traduction_sante_ai.html")
