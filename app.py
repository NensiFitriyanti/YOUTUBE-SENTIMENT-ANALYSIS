import streamlit as st
import pandas as pd
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from googleapiclient.discovery import build
from streamlit_autorefresh import st_autorefresh
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import base64
from io import BytesIO

# ================= LOAD API KEY =================
if "YOUTUBE_API_KEY" not in st.secrets:
    st.error("⚠️ API Key belum diatur di Streamlit Cloud → Secrets")
    st.stop()

API_KEY = st.secrets["YOUTUBE_API_KEY"]
youtube = build('youtube', 'v3', developerKey=API_KEY)
analyzer = SentimentIntensityAnalyzer()

st.set_page_config(page_title="📊 YouTube Sentiment Dashboard", layout="wide")

# ================== STYLE ==================
st.markdown("""
<style>
/* Judul Tengah */
h1 {
    text-align: center;
}

/* Menu rata kiri kanan */
.menu-container {
    display: flex;
    justify-content: space-between;
    padding: 10px 50px;
    margin-bottom: 20px;
}

/* Kotak komentar */
.comment-box {
    background: linear-gradient(145deg, #ffffff, #f0f0f0);
    border-radius: 15px;
    padding: 12px 18px;
    margin-bottom: 12px;
    box-shadow: 6px 6px 12px #d1d1d1, -6px -6px 12px #ffffff;
    transition: 0.3s ease-in-out;
}
.comment-box:hover {
    transform: translateY(-5px);
    box-shadow: 8px 8px 16px #c1c1c1, -8px -8px 16px #ffffff;
}

/* Insight box di tengah */
.insight-box {
    text-align: center;
    background: linear-gradient(145deg, #ffffff, #f8f8f8);
    border-radius: 20px;
    padding: 20px;
    margin: auto;
    width: 70%;
    box-shadow: 8px 8px 16px #d6d6d6, -8px -8px 16px #ffffff;
    transition: 0.3s ease-in-out;
}
.insight-box:hover {
    transform: scale(1.02);
}
</style>
""", unsafe_allow_html=True)

# ================== TITLE ==================
st.markdown("<h1>📊 YouTube Sentiment Analysis Dashboard</h1>", unsafe_allow_html=True)

# ================== MENU ==================
menu_left = st.selectbox("📂 Pilih Data", ["Tabel Komentar", "Grafik Komentar"])
menu_right = st.selectbox("📊 Pilih Visualisasi", ["Word Cloud", "Pie Chart"])

st.markdown("<div class='menu-container'></div>", unsafe_allow_html=True)

# ================== DATA YOUTUBE ==================
video_id = st.text_input("Masukkan YouTube Video ID:", "dQw4w9WgXcQ")

def get_comments(video_id):
    comments, sentiments = [], []
    request = youtube.commentThreads().list(part="snippet", videoId=video_id, maxResults=50, textFormat="plainText")
    response = request.execute()

    for item in response["items"]:
        comment = item["snippet"]["topLevelComment"]["snippet"]["textDisplay"]
        score = analyzer.polarity_scores(comment)
        comments.append(comment)
        sentiments.append(score)
    return pd.DataFrame(sentiments).assign(Comment=comments)

if video_id:
    df = get_comments(video_id)

    # ======== Tabel Komentar ========
    if menu_left == "Tabel Komentar":
        st.subheader("💬 Daftar Komentar")
        for _, row in df.iterrows():
            st.markdown(f"<div class='comment-box'><b>{row['Comment']}</b><br>😊 Positif: {row['pos']:.2f} | 😐 Netral: {row['neu']:.2f} | 😠 Negatif: {row['neg']:.2f}</div>", unsafe_allow_html=True)

    # ======== Grafik Komentar ========
    elif menu_left == "Grafik Komentar":
        st.subheader("📈 Grafik Komentar")
        st.line_chart(df[["pos", "neu", "neg"]])

    # ======== Word Cloud ========
    if menu_right == "Word Cloud":
        st.subheader("☁️ Word Cloud")
        text = " ".join(df["Comment"])
        wc = WordCloud(width=800, height=400, background_color="white").generate(text)
        fig, ax = plt.subplots()
        ax.imshow(wc, interpolation="bilinear")
        ax.axis("off")
        st.pyplot(fig)

    # ======== Pie Chart ========
    elif menu_right == "Pie Chart":
        st.subheader("📊 Distribusi Sentimen")
        labels = ["Positif", "Netral", "Negatif"]
        values = [df["pos"].mean(), df["neu"].mean(), df["neg"].mean()]
        fig, ax = plt.subplots()
        ax.pie(values, labels=labels, autopct='%1.1f%%', startangle=90)
        ax.axis("equal")
        st.pyplot(fig)

    # ======== Insight di Tengah ========
    st.markdown("<div class='insight-box'><h3>📌 Insight</h3><p>Mayoritas komentar bernuansa positif dengan sedikit komentar negatif. Analisis ini bisa dipakai untuk evaluasi konten.</p></div>", unsafe_allow_html=True)
