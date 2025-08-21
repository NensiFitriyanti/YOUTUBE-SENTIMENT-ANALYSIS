import streamlit as st
import pandas as pd
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from googleapiclient.discovery import build
from streamlit_autorefresh import st_autorefresh
from wordcloud import WordCloud
import matplotlib.pyplot as plt
from io import BytesIO
import re 
import gspread
from gspread_dataframe import set_with_dataframe, get_as_dataframe
import json

# ================= LOAD API KEY =================
if "YOUTUBE_API_KEY" not in st.secrets:
    st.error("⚠️ API Key belum diatur di Streamlit Cloud → Secrets")
    st.stop()

API_KEY = st.secrets["YOUTUBE_API_KEY"]

youtube = build('youtube', 'v3', developerKey=API_KEY)
analyzer = SentimentIntensityAnalyzer()

# ================= FUNCTION EXTRACT VIDEO ID =================
def extract_video_id(url_or_id):
    if re.match(r'^[\w-]{11}$', url_or_id):
        return url_or_id
    match = re.search(r'v=([\w-]{11})', url_or_id)
    if match:
        return match.group(1)
    match = re.search(r'youtu\.be/([\w-]{11})', url_or_id)
    if match:
        return match.group(1)
    return None

# ================= FUNCTION GET COMMENT =================
def get_comments(video_id, max_results=200):
    comments = []
    try:
        request = youtube.commentThreads().list(
            part='snippet',
            videoId=video_id,
            maxResults=100,
            textFormat="plainText",
            order="time"
        )
        while request and len(comments) < max_results:
            response = request.execute()
            for item in response['items']:
                comment = item['snippet']['topLevelComment']['snippet']['textDisplay']
                comments.append(comment)
            request = youtube.commentThreads().list_next(request, response)
    except Exception as e:
        st.error(f"Gagal ambil komentar: {e}")
    return comments[:max_results]

def analyze_sentiment(text):
    score = analyzer.polarity_scores(text)
    if score['compound'] >= 0.05:
        return 'Positif'
    elif score['compound'] <= -0.05:
        return 'Negatif'
    else:
        return 'Netral'

@st.cache_data(ttl=300)
def fetch_and_analyze(video_id):
    comments = get_comments(video_id)
    data = []
    for c in comments:
        label = analyze_sentiment(c)
        data.append({"VideoID": video_id, "Komentar": c, "Sentimen": label})
    return pd.DataFrame(data)

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

# ================= START MAIN CONTAINER =================
st.markdown("<div class='main-container'>", unsafe_allow_html=True)

# ================= STREAMLIT START =================
st.set_page_config(page_title="YouTube Sentiment Analysis", layout="wide")

# 🔄 AUTO REFRESH tiap 5 menit (300000 ms)
st_autorefresh(interval=300000, key="refresh_timer")

# 🎨 CSS Global Hover Effect (supaya tidak trigger rerun)
st.markdown("""
    <style>
    .hover-box:hover {
        transform: scale(1.05);
        transition: transform 0.3s ease;
    }
    </style>
""", unsafe_allow_html=True)

# ================= DEFAULT VIDEO INPUT =================
default_urls = [
    "https://youtu.be/Ugfjq0rDz8g?si=vWNO6nEAj9XB2LOB",
    "https://youtu.be/Lr1OHmBpwjw?si=9Mvu8o69V8Zt40yn",
    "https://youtu.be/5BFIAHBBdao?si=LPNB-8ZtJIk3xZVu",
    "https://youtu.be/UzAgIMvb3c0?si=fH01vTOsKuUb8IoF",
    "https://youtu.be/6tAZ-3FSYr0?si=rKhlEpS3oO7BOOtR",
    "https://youtu.be/M-Qsvh18JNM?si=JJZ2-RKikuexaNw5",
    "https://youtu.be/vSbe5C7BTuM?si=2MPkRB08C3P9Vilt",
    "https://youtu.be/Y7hcBMJDNwk?si=rI0-dsunElb5XMVl",
    "https://youtu.be/iySgErYzRR0?si=05mihs5jDRDXYgSZ",
    "https://youtu.be/gwEt2_yxTmc?si=rfBwVGhePy35YA5D",
    "https://youtu.be/9RCbgFi1idc?si=x7ILIEMAow5geJWS",
    "https://youtu.be/ZgkVHrihbXM?si=k8OittX6RL_gcgrd",
    "https://youtu.be/xvHiRY7skIk?si=nzAUYB71fQpLD2lv"
]

# langsung ambil video_ids dari default_urls
video_ids = [extract_video_id(v) for v in default_urls if extract_video_id(v)]

all_data = []
summary = {}

for vid in video_ids:
    df_video = fetch_and_analyze(vid)
    if not df_video.empty:
        all_data.append(df_video)
        summary[vid] = len(df_video)

if all_data:
    df = pd.concat(all_data, ignore_index=True)

    # ================= HEADER =================
    st.markdown(
        """
        <div style='display:flex; align-items:center;'>
            <div style='background-color:#FF0000; border-radius:15px; padding:15px; width:80px; height:80px;
                        display:flex; align-items:center; justify-content:center; box-shadow:5px 5px 15px rgba(0,0,0,0.3);'>
                <img src="https://upload.wikimedia.org/wikipedia/commons/b/b8/YouTube_Logo_2017.svg" width="60">
            </div>
            <h1 style='flex:1; text-align:center; color:black;'>YouTube Sentiment Analysis</h1>
        </div>
        """,
        unsafe_allow_html=True
    )

    # ================= STAT BOX PER VIDEO =================
    st.subheader("📊 Statistik Komentar per Video")
    colors = ["#FF9999", "#99CCFF", "#99FF99", "#FFD966", "#FFB266", "#CC99FF"]
    cols = st.columns(len(summary))
    for i, (vid, count) in enumerate(summary.items()):
        color = colors[i % len(colors)]
        with cols[i]:
            st.markdown(
                f"""
                <div class='hover-box' style='background-color:{color}; padding:20px; border-radius:15px; text-align:center;
                            box-shadow:2px 2px 10px rgba(0,0,0,0.2);'>
                    <h4 style='margin:0; color:black;'>Video {i+1}</h4>
                    <h2 style='margin:0; color:black;'>{count}</h2>
                    <p style='margin:0; color:black;'>Komentar</p>
                </div>
                """,
                unsafe_allow_html=True
            )

    # ================= 2 KOTAK PANJANG =================
    total_comments = len(df)
    st.markdown("### 📌 Ringkasan Keseluruhan")
    col1, col2 = st.columns(2)

    with col1:
        st.markdown(
            f"""
            <div class='hover-box' style='background-color:#f0f8ff; border-radius:15px; padding:25px; text-align:center;
                        box-shadow:3px 3px 12px rgba(0,0,0,0.2);'>
                <img src="https://cdn-icons-png.flaticon.com/512/709/709496.png" width="50">
                <h3>Total Komentar</h3>
                <h2 style='color:#FF0000;'>{total_comments}</h2>
                <p>100%</p>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col2:
        st.markdown(
            f"""
            <div class='hover-box' style='background-color:#f9f9f9; border-radius:15px; padding:25px; text-align:center;
                        box-shadow:3px 3px 12px rgba(0,0,0,0.2);'>
                <img src="https://cdn-icons-png.flaticon.com/512/747/747376.png" width="50">
                <h3>Total User</h3>
                <h2 style='color:#0073e6;'>{df['Komentar'].nunique()}</h2>
                <p>100%</p>
            </div>
            """,
            unsafe_allow_html=True
        )

    # ================= KOMENTAR & SENTIMEN + GRAFIK =================
    st.markdown("### 📋 Komentar, Sentimen dan Grafik Sentimen")
    col1, col2 = st.columns([2,1])
    with col1:
        st.dataframe(df)
    with col2:
        st.bar_chart(df['Sentimen'].value_counts())

    # ================= WORDCLOUD + PIE CHART =================
    st.markdown("### ☁️ Word Cloud & Pie Chart")
    col1, col2 = st.columns(2)

    with col1:
        all_text = " ".join(df["Komentar"].tolist())
        all_text = all_text.encode("utf-8", "ignore").decode("utf-8")
        if all_text.strip():
            wordcloud = WordCloud(width=800, height=400, background_color="white").generate(all_text)
            fig_wc, ax = plt.subplots(figsize=(10, 5))
            ax.imshow(wordcloud, interpolation="bilinear")
            ax.axis("off")
            st.pyplot(fig_wc)

    with col2:
        sentiment_counts = df['Sentimen'].value_counts()
        fig, ax = plt.subplots()
        wedges, texts, autotexts = ax.pie(
            sentiment_counts, labels=sentiment_counts.index, autopct='%1.1f%%', startangle=90, shadow=True
        )
        ax.axis("equal")
        st.pyplot(fig)

    # ================= DOWNLOAD BUTTONS =================
    st.markdown("### ⬇️ Unduh Hasil")
    csv = df.to_csv(index=False).encode('utf-8')
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name="Sentimen")

    col1, col2 = st.columns(2)
    with col1:
        st.download_button("Download CSV", csv, "sentimen_youtube.csv", "text/csv")
    with col2:
        st.download_button("Download Excel", output.getvalue(), "sentimen_youtube.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

else:
    st.warning("Komentar tidak ditemukan atau ID salah.")
    # ================= END MAIN CONTAINER =================
st.markdown("</div>", unsafe_allow_html=True)