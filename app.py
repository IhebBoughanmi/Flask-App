from flask import Flask, request, jsonify
from bs4 import BeautifulSoup, Comment
from readability import Document
import requests
from html import escape
from deep_translator import GoogleTranslator

app = Flask(__name__)

def extract_main_article(url):
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:125.0) Gecko/20100101 Firefox/125.0'
        }
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        original_html = response.text
        soup_original = BeautifulSoup(original_html, 'html.parser')

        # Extract the best title candidate
        article_title = ""
        meta_title = soup_original.find('meta', property='og:title')
        if meta_title and meta_title.get('content'):
            article_title = meta_title['content']
        elif soup_original.find('title'):
            article_title = soup_original.find('title').get_text().strip()
        elif soup_original.find('h1'):
            article_title = soup_original.find('h1').get_text().strip()

        # Extract the main content
        doc = Document(original_html)
        main_content = doc.summary()
        soup_main = BeautifulSoup(main_content, 'html.parser')

        # Insert raw title as <h1>
        if article_title:
            title_tag = soup_main.new_tag('h1')
            title_tag.string = article_title
            soup_main.insert(0, title_tag)

        paragraphs = [p.get_text().strip() for p in soup_main.find_all('p') if p.get_text().strip()]
        return article_title, paragraphs

    except Exception as e:
        raise RuntimeError(f"Failed to extract article: {str(e)}")


@app.route('/translate', methods=['POST'])
def translate_article():
    data = request.get_json()
    url = data.get('url')
    lang_from = data.get('lang_from', 'auto')
    lang_to = data.get('lang_to', 'ar')

    if not url:
        return jsonify({"error": "Missing 'url' parameter"}), 400

    try:
        title, paragraphs = extract_main_article(url)

        # Translate the title
        translated_title = GoogleTranslator(source=lang_from, target=lang_to).translate(title)

        html = f"""<!DOCTYPE html>
<html lang="{lang_to}">
<head>
    <meta charset="UTF-8">
    <title>{escape(translated_title)}</title>
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
    <h1>{escape(translated_title)}</h1>
"""

        for p in paragraphs:
            try:
                translated = GoogleTranslator(source=lang_from, target=lang_to).translate(p)
                html += f"<p>{escape(translated)}</p>\n"
            except Exception:
                html += f'<p class="original">[NON TRADUIT] {escape(p)}</p>\n'

        html += "</body></html>"

        with open("/tmp/translated_article.html", "w", encoding="utf-8") as f:
            f.write(html)

        return jsonify({
            "message": "Translation completed",
            "download_url": request.host_url + "download"
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/download', methods=['GET'])
def download_translated_file():
    try:
        with open("/tmp/translated_article.html", "r", encoding="utf-8") as f:
            return f.read(), 200, {
                'Content-Type': 'text/html; charset=utf-8'
            }
    except:
        return jsonify({"error": "No file found. Translate something first."}), 404


if __name__ == '__main__':
    app.run(debug=True)
