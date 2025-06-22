from flask import Flask, request, jsonify
from bs4 import BeautifulSoup
from readability import Document
import requests
from html import escape
from deep_translator import GoogleTranslator

app = Flask(__name__)

def extract_main_article(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # Extract title
        title = ''
        meta_title = soup.find('meta', property='og:title')
        if meta_title and meta_title.get('content'):
            title = meta_title['content']
        elif soup.find('title'):
            title = soup.find('title').get_text().strip()

        # Extract readable content
        readable_article = Document(response.text)
        content_html = readable_article.summary()
        content_soup = BeautifulSoup(content_html, 'html.parser')
        paragraphs = [p.get_text().strip() for p in content_soup.find_all('p') if p.get_text().strip()]

        return title, paragraphs
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

        html = f"""<!DOCTYPE html>
<html lang="{lang_to}">
<head>
    <meta charset="UTF-8">
    <title>{escape(title)}</title>
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
    <h1>{escape(title)}</h1>
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
