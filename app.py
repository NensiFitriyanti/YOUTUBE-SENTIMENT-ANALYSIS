import streamlit as st
import pandas as pd
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from googleapiclient.discovery import build
from streamlit_autorefresh import st_autorefresh
import matplotlib.pyplot as plt
from wordcloud import WordCloud
import base64
from io import BytesIO

# ================= LOAD API KEY =================
if "YOUTUBE_API_KEY" not in st.secrets:
    st.error("⚠️ API Key belum diatur di Streamlit Cloud → Secrets")
    st.stop()

API_KEY = st.secrets["YOUTUBE_API_KEY"]
youtube = build('youtube', 'v3', developerKey=API_KEY)
analyzer = SentimentIntensityAnalyzer()

# ================= AUTO REFRESH (5 menit) =================
st_autorefresh(interval=300000, key="refresh_timer")  # 300000 ms = 5 menit

# ================= CSS GLOBAL =================
st.markdown("""
    <style>
    /* Background kotak besar */
    .main-container {
        background-color: #ffffff;
        padding: 25px;
        border-radius: 20px;
        box-shadow: 0px 4px 20px rgba(0,0,0,0.2);
        margin: 20px auto;
        max-width: 1200px;
    }

    /* Hover untuk stat box */
    .hover-box:hover {
        transform: scale(1.05);
        transition: transform 0.3s ease;
    }
    </style>
""", unsafe_allow_html=True)

# ================= MULAI MAIN CONTAINER =================
st.markdown("<div class='main-container'>", unsafe_allow_html=True)

# Judul Dashboard
st.title("📊 YouTube Sentiment Analysis Dashboard")

# ================= VIDEO YANG DITETAPKAN LANGSUNG =================
VIDEO_ID = "VIDEO_ID_OR_LINK_KAMU"  # 🔴 ganti dengan ID video atau link langsung

# ================= AMBIL KOMENTAR =================
def get_comments(video_id, max_results=50):
    comments = []
    results = youtube.commentThreads().list(
        part="snippet",
        videoId=video_id,
        maxResults=max_results,
        textFormat="plainText"
    ).execute()

    for item in results["items"]:
        comment = item["snippet"]["topLevelComment"]["snippet"]["textDisplay"]
        comments.append(comment)

    return comments

comments = get_comments(VIDEO_ID, max_results=100)

# ================= ANALISIS SENTIMEN =================
data = []
for c in comments:
    score = analyzer.polarity_scores(c)
    if score['compound'] >= 0.05:
        sentiment = "Positif"
    elif score['compound'] <= -0.05:
        sentiment = "Negatif"
    else:
        sentiment = "Netral"
    data.append({"Komentar": c, "Sentimen": sentiment})

df = pd.DataFrame(data)

# ================= STAT BOX =================
col1, col2, col3 = st.columns(3)
with col1:
    st.markdown(f"""
        <div class='hover-box' style='background-color:#f5f5f5; padding:20px; 
        border-radius:15px; text-align:center; box-shadow:2px 2px 10px rgba(0,0,0,0.2);'>
            <h4 style='margin:0; color:black;'>Total Komentar</h4>
            <h2 style='margin:0; color:black;'>{len(df)}</h2>
        </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
        <div class='hover-box' style='background-color:#d4edda; padding:20px; 
        border-radius:15px; text-align:center; box-shadow:2px 2px 10px rgba(0,0,0,0.2);'>
            <h4 style='margin:0; color:black;'>Positif</h4>
            <h2 style='margin:0; color:black;'>{len(df[df['Sentimen']=='Positif'])}</h2>
        </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
        <div class='hover-box' style='background-color:#f8d7da; padding:20px; 
        border-radius:15px; text-align:center; box-shadow:2px 2px 10px rgba(0,0,0,0.2);'>
            <h4 style='margin:0; color:black;'>Negatif</h4>
            <h2 style='margin:0; color:black;'>{len(df[df['Sentimen']=='Negatif'])}</h2>
        </div>
    """, unsafe_allow_html=True)

# ================= PIE CHART =================
st.subheader("📌 Distribusi Sentimen")
fig, ax = plt.subplots()
df['Sentimen'].value_counts().plot.pie(autopct='%1.1f%%', ax=ax)
st.pyplot(fig)

# ================= WORDCLOUD =================
st.subheader("☁️ Word Cloud Komentar")
text = " ".join(df["Komentar"].tolist())
wordcloud = WordCloud(width=800, height=400, background_color="white").generate(text)

fig, ax = plt.subplots(figsize=(10, 5))
ax.imshow(wordcloud, interpolation="bilinear")
ax.axis("off")
st.pyplot(fig)

# ================= TABEL =================
st.subheader("📋 Data Komentar & Sentimen")
st.dataframe(df)

# ================= END MAIN CONTAINER =================
st.markdown("</div>", unsafe_allow_html=True)