# streamlit_app.py
# Etik ve login gerektirmeyen Instagram public istatistik dashboard'u

import instaloader
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

# -------------------- STREAMLIT AYARLARI --------------------
st.set_page_config(
    page_title="InStatistics",
    layout="wide"
)

plt.rcParams.update({
    "figure.facecolor": "#0e1117",
    "axes.facecolor": "#0e1117",
    "axes.edgecolor": "#444444",
    "axes.labelcolor": "#e6e6e6",
    "text.color": "#e6e6e6",
    "xtick.color": "#e6e6e6",
    "ytick.color": "#e6e6e6",
    "grid.color": "#2a2a2a",
    "font.size": 11
})

# -------------------- BAŞLIK --------------------
st.title("📊 InStatistics-Instagram Hesap İstatistikleri")
st.caption("Login yok  •  Kişisel veri yok  •  Sadece public metadata")

# -------------------- KULLANICI GİRDİLERİ --------------------
username = st.text_input(
    "Instagram kullanıcı adı",
    placeholder="ornekhesap"
)

max_posts = st.slider(
    "Analiz edilecek maksimum gönderi",
    min_value=50,
    max_value=1000,
    value=500,
    step=50
)

# -------------------- VERİ ÇEKME --------------------
@st.cache_data(show_spinner=False)
def fetch_posts(username: str, max_posts: int) -> pd.DataFrame:
    L = instaloader.Instaloader(
        download_pictures=False,
        download_videos=False,
        download_video_thumbnails=False,
        save_metadata=False,
        compress_json=False
    )

    profile = instaloader.Profile.from_username(L.context, username)

    data = []
    for i, post in enumerate(profile.get_posts()):
        if i >= max_posts:
            break

        data.append({
            "date": post.date,
            "likes": post.likes,
            "comments": post.comments,
            "is_video": post.is_video
        })

    df = pd.DataFrame(data)
    df["date"] = pd.to_datetime(df["date"])
    return df


# -------------------- ANA AKIŞ --------------------
if not username:
    st.info("Başlamak için bir Instagram kullanıcı adı gir")
    st.stop()

with st.spinner("Veriler toplanıyor..."):
    try:
        df = fetch_posts(username, max_posts)
    except Exception:
        st.error("Hesap bulunamadı veya erişilemedi")
        st.stop()

if df.empty:
    st.warning("Analiz edilecek veri bulunamadı")
    st.stop()

st.success(f"{len(df)} gönderi analiz edildi")

# -------------------- ZORUNLU TÜREV KOLONLAR --------------------
df["date_only"] = df["date"].dt.date
df["hour"] = df["date"].dt.hour
df["weekday"] = df["date"].dt.day_name()

# -------------------- GENEL METRİKLER --------------------
c1, c2, c3, c4 = st.columns(4)

c1.metric("Toplam Gönderi", len(df))
c2.metric("Günlük Ortalama", round(df.groupby("date_only").size().mean()))
c3.metric("Haftalık Ortalama", round(df.groupby(df["date"].dt.to_period("W")).size().mean()))
c4.metric("Video Oranı", f"%{round(df['is_video'].mean() * 100, 1)}")

# -------------------- SAATLİK DAĞILIM --------------------
st.subheader("🕒 Saatlik Paylaşım Dağılımı")

# Saat bazlı sayım
hourly = df["hour"].value_counts().sort_index()

# ❗ 0 gönderi olan saatleri çıkar
hourly = hourly[hourly > 0]

fig_h, ax_h = plt.subplots(figsize=(8, 4))
ax_h.bar(hourly.index, hourly.values)

ax_h.set_xlabel("Saat")
ax_h.set_ylabel("Gönderi Sayısı")

# Sadece veri olan saatleri göster
ax_h.set_xticks(hourly.index)
ax_h.set_xticklabels(hourly.index)

ax_h.grid(axis="y", linestyle="--", alpha=0.3)

plt.tight_layout()
st.pyplot(fig_h)


# -------------------- HAFTANIN GÜNLERİ --------------------
st.subheader("📅 Haftanın Günlerine Göre Paylaşım")

weekday_order = [
    "Monday", "Tuesday", "Wednesday",
    "Thursday", "Friday", "Saturday", "Sunday"
]

weekday_counts = (
    df["weekday"]
    .value_counts()
    .reindex(weekday_order)
    .fillna(0)
)

fig_w, ax_w = plt.subplots(figsize=(8, 4))
bars = ax_w.bar(weekday_counts.index, weekday_counts.values)

ax_w.set_ylabel("Gönderi Sayısı")
ax_w.grid(axis="y", linestyle="--", alpha=0.3)
ax_w.spines["top"].set_visible(False)
ax_w.spines["right"].set_visible(False)

for bar in bars:
    ax_w.text(
        bar.get_x() + bar.get_width() / 2,
        bar.get_height(),
        int(bar.get_height()),
        ha="center",
        va="bottom"
    )

plt.tight_layout()
st.pyplot(fig_w)

# -------------------- AYLIK RAPOR --------------------
st.subheader("📅 Aylık Gönderi Raporu")

monthly = df.groupby(df["date"].dt.to_period("M")).size()

# İlk ay eksikse temizle
if len(monthly) >= 2:
    if abs(monthly.iloc[0] - monthly.iloc[1]) / max(monthly.iloc[1], 1) > 0.5:
        monthly = monthly.iloc[1:]

monthly_df = monthly.rename("Gönderi Sayısı").reset_index()
st.dataframe(monthly_df, use_container_width=True)

fig_m, ax_m = plt.subplots(figsize=(8, 4))
ax_m.plot(monthly.index.astype(str), monthly.values, marker="o")
ax_m.set_ylabel("Gönderi Sayısı")
ax_m.grid(True, linestyle="--", alpha=0.3)
plt.tight_layout()
st.pyplot(fig_m)

# -------------------- CSV --------------------
st.subheader("📁 Veri Dışa Aktarma")

csv = df.to_csv(index=False).encode("utf-8")
st.download_button(
    "CSV olarak indir",
    csv,
    f"{username}_instagram_stats.csv",
    "text/csv"
)

