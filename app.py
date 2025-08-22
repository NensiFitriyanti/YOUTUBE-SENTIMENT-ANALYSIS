import streamlit as st
import pandas as pd
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from googleapiclient.discovery import build
from streamlit_autorefresh import st_autorefresh
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import re 

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
    /* ===== Menu Style ===== */
    div[role=radiogroup] {
        display: flex;
        justify-content: center;
        gap: 30px;
        margin-bottom: 25px;
    }
    div[role=radiogroup] label {
        background: #f5f5f5;
        padding: 12px 25px;
        border-radius: 12px;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.1);
        cursor: pointer;
        transition: all 0.3s ease;
    }
    div[role=radiogroup] label:hover {
        background: #e0e0e0;
        transform: scale(1.05);
    }

    /* ===== Stat Box per Video ===== */
    .video-box {
        background: #ffffff;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.15);
        text-align: center;
        margin: 10px;
    }

    /* ===== Ringkasan Total ===== */
    .big-box {
        background: linear-gradient(135deg, #99CCFF, #99FFCC);
        padding: 25px;
        border-radius: 20px;
        text-align: center;
        color: black;
        font-weight: bold;
        box-shadow: 0 4px 20px rgba(0,0,0,0.2);
    }
    .big-box h2 {
        margin: 0;
        font-size: 2.2em;
    }
    .big-box p {
        margin: 5px 0 0;
        font-size: 1.1em;
    }

    /* ===== Main Container ===== */
    .main-container {
        background-color: #ffffff;
        padding: 25px;
        border-radius: 20px;
        box-shadow: 0px 4px 20px rgba(0,0,0,0.2);
        margin: 20px auto;
        max-width: 1200px;
    }
    </style>
""", unsafe_allow_html=True)

# ================= START MAIN =================
st.set_page_config(page_title="YouTube Sentiment Analysis", layout="wide")
st_autorefresh(interval=300000, key="refresh_timer")

# ================= HEADER & MENU =================
st.markdown("<h1 style='text-align:center;'>YOUTUBE SENTIMENT ANALYSIS</h1>", unsafe_allow_html=True)

menu = st.radio(
    "Pilih Menu",
    ["Dashboard Komentar", "Grafik Komentar", "Wordcloud", "Insight & Rekomendasi"],
    horizontal=True
)

# ================= DATA PREP =================
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
video_ids = [extract_video_id(v) for v in default_urls if extract_video_id(v)]

all_data, summary = [], {}
for vid in video_ids:
    df_video = fetch_and_analyze(vid)
    if not df_video.empty:
        all_data.append(df_video)
        summary[vid] = len(df_video)

df = pd.concat(all_data, ignore_index=True) if all_data else pd.DataFrame()

# ================= HALAMAN =================
if menu == "Dashboard Komentar":
    if df.empty:
        st.warning("Komentar tidak ditemukan.")
    else:
        st.subheader("📊 Statistik Komentar per Video")

        # tampilkan 3 per baris
        cols_per_row = 3
        video_items = list(summary.items())
        for row_start in range(0, len(video_items), cols_per_row):
            row_items = video_items[row_start: row_start+cols_per_row]
            cols = st.columns(len(row_items))
            for i, (vid, count) in enumerate(row_items):
                with cols[i]:
                    st.markdown(
                        f"""
                        <div class="video-box">
                            <h4>Video {row_start+i+1}</h4>
                            <h2>{count}</h2>
                            <p>Komentar</p>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

        # === RINGKASAN KESELURUHAN ===
        total_comments = len(df)
        total_users = df['Komentar'].nunique()
        st.markdown("### 📌 Ringkasan Keseluruhan")

        col1, col2 = st.columns(2)
        with col1:
            st.markdown(
                f"""
                <div class="big-box">
                    <h2>💬 {total_comments}</h2>
                    <p>Total Komentar</p>
                </div>
                """, unsafe_allow_html=True
            )
        with col2:
            st.markdown(
                f"""
                <div class="big-box">
                    <h2>👥 {total_users}</h2>
                    <p>Total User</p>
                </div>
                """, unsafe_allow_html=True
            )

elif menu == "Grafik Komentar":
    st.markdown("### 📋 Komentar & Sentimen")
    st.markdown("<div class='main-container'>", unsafe_allow_html=True)
    col1, col2 = st.columns([2,1])
    with col1:
        st.dataframe(df)
    with col2:
        st.bar_chart(df['Sentimen'].value_counts())
    st.markdown("</div>", unsafe_allow_html=True)

elif menu == "Wordcloud":
    st.markdown("### ☁️ Word Cloud & Pie Chart")
    st.markdown("<div class='main-container'>", unsafe_allow_html=True)
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
        ax.pie(sentiment_counts, labels=sentiment_counts.index, autopct='%1.1f%%', startangle=90, shadow=True)
        ax.axis("equal")
        st.pyplot(fig)
    st.markdown("</div>", unsafe_allow_html=True)

elif menu == "Insight & Rekomendasi":
    st.subheader("📊 Insight Sentimen")
    total, positif, negatif, netral = len(df), (df['Sentimen']=='Positif').sum(), (df['Sentimen']=='Negatif').sum(), (df['Sentimen']=='Netral').sum()
    st.markdown("<div class='main-container'>", unsafe_allow_html=True)
    st.write(f"Total komentar dianalisis: **{total}**")
    st.write(f"Positif: **{positif}** | Negatif: **{negatif}** | Netral: **{netral}**")
    if positif > negatif:
        st.success("Mayoritas komentar positif 🎉. Konten disukai audiens.")
    elif negatif > positif:
        st.error("Komentar negatif lebih dominan ⚠️. Perlu evaluasi konten.")
    else:
        st.info("Komentar seimbang. Bisa ditingkatkan dengan interaksi lebih aktif.")

    st.subheader("💡 Rekomendasi")
    st.markdown("""
    - Tingkatkan interaksi dengan penonton (balas komentar, adakan Q&A).  
    - Perhatikan topik/kata dominan yang disukai.  
    - Jika komentar negatif banyak, evaluasi kualitas video & penyampaian.  
    - Gunakan feedback untuk konten berikutnya.  
    """)
    st.markdown("</div>", unsafe_allow_html=True)