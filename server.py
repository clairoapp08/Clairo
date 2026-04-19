import os
import json
import requests

NEWS_API_KEY = os.environ.get("NEWS_API_KEY", "6ff731d44dba4b7eb469b4d70f333f58")
def get_news_headlines(symbol):
    try:
        url = f"https://newsapi.org/v2/everything?q={symbol}&language=en&sortBy=publishedAt&pageSize=3&apiKey={NEWS_API_KEY}"
        response = requests.get(url, timeout=5)
        data = response.json()
        headlines = []
        for article in data.get("articles", []):
            headlines.append(article["title"])
        return headlines
    except:
        return []
import yfinance as yf
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

ANTHROPIC_KEY = (os.environ.get("ANTHROPIC_KEY") or os.environ.get("ANTHROPIC_API_KEY", "")).strip()

def get_stock_data(symbol):
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period="1d")
        if hist.empty:
            return None
        price = round(hist['Close'].iloc[-1], 2)
        open_price = round(hist['Open'].iloc[-1], 2)
        change_pct = round(((price - open_price) / open_price) * 100, 2)
        return {"price": str(price), "change": str(change_pct)}
    except Exception as e:
        print(f"Stock error: {e}")
        return None

def get_ai_summary(symbol, price, change):
    try:
        direction = "up" if float(change) >= 0 else "down"
        headlines = get_news_headlines(symbol)
        news_context = ""
        if headlines:
            news_context = "Recent headlines: " + " | ".join(headlines[:3])
        headers = {
            "x-api-key": ANTHROPIC_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        body = {
            "model": "claude-haiku-4-5-20251001",
            "max_tokens": 150,
            "messages": [{
                "role": "user",
                "content": f"""You are a stock analyst writing short summaries for beginner investors. Write exactly 2 sentences about {symbol} stock. Today it moved {direction} {abs(float(change))}% to ${price}.

{news_context}

Sentence 1: Based on the price movement and the news headlines provided, give a specific concrete reason for today's move. Reference the actual news if available.
Sentence 2: Name one specific thing to watch for this stock based on current news and the company's business.

No jargon. No markdown. No bullet points. Exactly 2 sentences. Never say you lack real-time data. Never refuse. Always write something useful. Never mention you are an AI."""
            }]
        }
        response = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers=headers,
            json=body,
            timeout=30
        )
        data = response.json()
        return data["content"][0]["text"]
    except Exception as e:
        print(f"AI error: {e}")
        return f"{symbol} moved {change}% today. Check financial news for the latest updates."
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)

        if parsed.path == "/" or parsed.path == "/dashboard":
            self.serve_file("dashboard.html", "text/html")
            return

        if parsed.path == "/api/stock":
            params = parse_qs(parsed.query)
            symbol = params.get("symbol", [""])[0].upper()
            if not symbol:
                self.send_json({"error": "No symbol"}, 400)
                return
            data = get_stock_data(symbol)
            if not data:
                self.send_json({"price": "N/A", "change": "0", "summary": "Could not load data. Markets may be closed."})
                return
            summary = get_ai_summary(symbol, data["price"], data["change"])
            self.send_json({"price": data["price"], "change": data["change"], "summary": summary})
            return

        self.send_error(404)

    def serve_file(self, filename, content_type):
        try:
            with open(filename, "rb") as f:
                content = f.read()
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.end_headers()
            self.wfile.write(content)
        except FileNotFoundError:
            self.send_error(404)

    def send_json(self, data, code=200):
        content = json.dumps(data).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(content)

    def log_message(self, format, *args):
        pass

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    print(f"Clairo server running at http://localhost:{port}")
    HTTPServer(("", port), Handler).serve_forever()