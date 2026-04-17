import streamlit as st
import requests
import anthropic

ALPHA_VANTAGE_KEY = "your_alpha_vantage_key"
ANTHROPIC_KEY = " your_anthropic_key"

st.set_page_config(page_title="Clairo", page_icon="📈", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .stApp { background-color: #0a0a0a; }
    
    section[data-testid="stSidebar"] {
        background-color: #0f0f0f;
        border-right: 1px solid #1a1a1a;
    }
    section[data-testid="stSidebar"] * { color: #888 !important; }
    section[data-testid="stSidebar"] .stTextInput input {
        background-color: #1a1a1a !important;
        border: 1px solid #222 !important;
        color: #fff !important;
        border-radius: 6px !important;
    }

    .clairo-header { 
        padding: 40px 0 8px; 
    }
    .clairo-title {
        font-size: 32px;
        font-weight: 800;
        color: #ffffff;
        letter-spacing: -1px;
        margin-bottom: 4px;
    }
    .clairo-title span { color: #00c896; }
    .clairo-sub {
        color: #444;
        font-size: 14px;
        margin-bottom: 32px;
    }

    .stock-card {
        background: #0f0f0f;
        border: 1px solid #1a1a1a;
        border-radius: 12px;
        padding: 28px;
        margin-bottom: 16px;
        transition: border-color 0.2s;
    }
    .stock-card:hover { border-color: #2a2a2a; }
    .stock-symbol {
        font-size: 13px;
        font-weight: 700;
        color: #555;
        letter-spacing: 1.5px;
        text-transform: uppercase;
        margin-bottom: 8px;
    }
    .stock-price {
        font-size: 28px;
        font-weight: 800;
        color: #ffffff;
        letter-spacing: -0.5px;
        margin-bottom: 6px;
    }
    .change-up {
        font-size: 13px;
        font-weight: 600;
        color: #00c896;
        margin-bottom: 16px;
    }
    .change-down {
        font-size: 13px;
        font-weight: 600;
        color: #ff4d4d;
        margin-bottom: 16px;
    }
    .stock-summary {
        font-size: 13px;
        color: #555;
        line-height: 1.7;
        border-top: 1px solid #1a1a1a;
        padding-top: 16px;
    }

    .section-label {
        font-size: 11px;
        font-weight: 700;
        color: #333;
        letter-spacing: 1.5px;
        text-transform: uppercase;
        margin-bottom: 20px;
    }

    div[data-testid="stTextInput"] input {
        background-color: #0f0f0f !important;
        border: 1px solid #1a1a1a !important;
        color: #fff !important;
        border-radius: 8px !important;
        font-family: 'Inter', sans-serif !important;
    }
    div[data-testid="stTextInput"] label {
        color: #444 !important;
        font-size: 12px !important;
    }
    .stButton button {
        background-color: #00c896 !important;
        color: #0a0a0a !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 700 !important;
        font-size: 13px !important;
        padding: 8px 20px !important;
    }
    .stButton button:hover { opacity: 0.9 !important; }
    
    div[data-testid="stMarkdownContainer"] h3 { display: none; }
    .stSpinner { color: #333 !important; }
    footer { display: none !important; }
    #MainMenu { display: none !important; }
    header { display: none !important; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="clairo-header">
    <div class="clairo-title"><span>Clairo</span></div>
    <div class="clairo-sub">Your daily AI-powered stock digest — simple, clear, and fast.</div>
</div>
""", unsafe_allow_html=True)

st.sidebar.markdown("### Watchlist")
st.sidebar.markdown("Track up to 5 stocks.")
stock_inputs = []
for i in range(5):
    symbol = st.sidebar.text_input(f"Stock {i+1}", value="", key=f"stock_{i}")
    if symbol.strip():
        stock_inputs.append(symbol.strip().upper())

if not stock_inputs:
    stock_inputs = ["AAPL", "TSLA", "NVDA", "GOOGL", "META"]

search_query = st.text_input("Search a stock", placeholder="e.g. AAPL, TSLA, GOOGL...")
search_btn = st.button("Search")

def get_stock_data(symbol):
    url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={ALPHA_VANTAGE_KEY}"
    r = requests.get(url)
    data = r.json()
    quote = data.get("Global Quote", {})
    return {
        "price": quote.get("05. price", "N/A"),
        "change": quote.get("10. change percent", "N/A")
    }

def get_news(symbol):
    url = f"https://www.alphavantage.co/query?function=NEWS_SENTIMENT&tickers={symbol}&limit=3&apikey={ALPHA_VANTAGE_KEY}"
    r = requests.get(url)
    data = r.json()
    articles = data.get("feed", [])
    headlines = [a["title"] for a in articles[:3]]
    return headlines

def get_ai_summary(symbol, price, change, headlines):
    client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)
    news_text = "\n".join(headlines) if headlines else "No recent news."
    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=200,
        messages=[{
            "role": "user",
            "content": f"Stock: {symbol}\nPrice: ${price}\nChange today: {change}\nRecent headlines:\n{news_text}\n\nWrite a 3 sentence plain English summary for a beginner investor. What happened, why it matters, and what to watch. Do not use any markdown, headers, or hashtags. Plain text only."
        }]
    )
    return message.content[0].text

def render_stock_card(symbol):
    stock = get_stock_data(symbol)
    news = get_news(symbol)
    summary = get_ai_summary(symbol, stock["price"], stock["change"], news)
    change_str = stock["change"].replace("%", "").strip()
    try:
        change_val = float(change_str)
        change_class = "change-up" if change_val >= 0 else "change-down"
        arrow = "▲" if change_val >= 0 else "▼"
    except:
        change_class = "change-up"
        arrow = ""
    st.markdown(
        '<div class="stock-card">'
        '<div class="stock-symbol">' + symbol + '</div>'
        '<div class="stock-price">$' + stock["price"] + '</div>'
        '<div class="' + change_class + '">' + arrow + ' ' + stock["change"] + '</div>'
        '<div class="stock-summary">' + summary + '</div>'
        '</div>',
        unsafe_allow_html=True
    )

if search_btn and search_query.strip():
    st.markdown('<div class="section-label">Search Results</div>', unsafe_allow_html=True)
    render_stock_card(search_query.strip().upper())

st.markdown('<div class="section-label">Your Watchlist</div>', unsafe_allow_html=True)
cols = st.columns(2)
for i, symbol in enumerate(stock_inputs):
    with cols[i % 2]:
        render_stock_card(symbol)