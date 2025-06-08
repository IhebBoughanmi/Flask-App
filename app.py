from flask import Flask, request, jsonify
from newspaper import Article
from deep_translator import GoogleTranslator
from html import escape
import os

app = Flask(__name__)

@app.route('/translate', methods=['POST'])
def translate_article():
    data = request.get_json()
    url = data.get('url')
    lang_from = data.get('lang_from', 'auto')
    lang_to = data.get('lang_to', 'ar')

    if not url:
        return jsonify({"error": "Missing 'url' parameter"}), 400

    try:
        article = Article(url)
        article.download()
        article.parse()

        title = article.title.strip()
        paragraphs = [p.strip() for p in article.text.split('\n') if p.strip()]

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

        for i, p in enumerate(paragraphs):
            try:
                translated = GoogleTranslator(source=lang_from, target=lang_to).translate(p)
                html += f"<p>{escape(translated)}</p>\n"
            except Exception as e:
                html += f'<p class="original">[NON TRADUIT] {escape(p)}</p>\n'

        html += "</body></html>"

        # Save file
        output_path = f"/tmp/translated_article.html"
        with open(output_path, "w", encoding="utf-8") as f:
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
    except Exception as e:
        return jsonify({"error": "No file found. Translate something first."}), 404


if __name__ == '__main__':
    app.run()
