import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

# -------------------- SAYFA AYAR --------------------
st.set_page_config(
    page_title="InStatistics-Instagram İstatistik Sayfası",
    layout="wide"
)

# -------------------- DARK THEME --------------------
plt.rcParams.update({
    "figure.facecolor": "#0e1117",
    "axes.facecolor": "#0e1117",
    "axes.edgecolor": "#444",
    "axes.labelcolor": "#e6e6e6",
    "text.color": "#e6e6e6",
    "xtick.color": "#e6e6e6",
    "ytick.color": "#e6e6e6",
    "grid.color": "#2a2a2a",
    "font.size": 11
})

# -------------------- BAŞLIK --------------------
st.title("📊 Instagram Public İstatistik Dashboard")
st.caption("CSV tabanlı • Çok hızlı • Doğru sonuçlar")

# -------------------- DOSYA YÜKLE --------------------
uploaded_file = st.file_uploader(
    "Instagram gönderi CSV dosyanı yükle",
    type="csv"
)

if not uploaded_file:
    st.info("Başlamak için bir CSV dosyası yükle")
    st.stop()

# -------------------- VERİ OKUMA --------------------
@st.cache_data
def load_data(file):
    df = pd.read_csv(file)
    df["date"] = pd.to_datetime(df["date"])
    df["hour"] = df["date"].dt.hour
    df["weekday"] = df["date"].dt.day_name()
    df["month"] = df["date"].dt.to_period("M")
    return df

df = load_data(uploaded_file)

st.success(f"{len(df)} gönderi yüklendi")

# -------------------- GENEL METRİKLER --------------------
c1, c2, c3, c4 = st.columns(4)

c1.metric("Toplam Gönderi", len(df))
c2.metric("Ortalama Beğeni", int(df["likes"].mean()))
c3.metric("Ortalama Yorum", int(df["comments"].mean()))
c4.metric("Video Oranı", f"%{round(df['is_video'].mean()*100,1)}")

# -------------------- GÜN BAZLI ARALIK --------------------
st.subheader("⏱️ Paylaşım Aralığı (Gün Bazlı)")

unique_days = (
    df["date"].dt.date
    .drop_duplicates()
    .sort_values()
)

day_diffs = unique_days.diff().dropna().apply(lambda x: x.days)

if len(day_diffs):
    st.write(f"**Ortalama paylaşım aralığı:** {round(day_diffs.mean())} gün")
else:
    st.write("Yetersiz veri")

# -------------------- SAATLİK DAĞILIM --------------------
st.subheader("🕒 Saatlik Paylaşım Dağılımı")

hourly = (
    df["hour"]
    .value_counts()
    .sort_index()
)

# 0 olan saatleri çıkar
hourly = hourly[hourly > 0]

fig_h, ax_h = plt.subplots(figsize=(9, 4))
ax_h.bar(hourly.index, hourly.values)
ax_h.set_xticks(hourly.index)  # TAM SAATLER
ax_h.set_xlabel("Saat")
ax_h.set_ylabel("Gönderi Sayısı")
ax_h.grid(axis="y", linestyle="--", alpha=0.3)
st.pyplot(fig_h)

# -------------------- HAFTANIN GÜNLERİ --------------------
st.subheader("📅 Haftanın Günlerine Göre Paylaşım")

order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

weekday_counts = (
    df["weekday"]
    .value_counts()
    .reindex(order)
)

fig_w, ax_w = plt.subplots(figsize=(9, 4))
ax_w.bar(weekday_counts.index, weekday_counts.values)
ax_w.set_ylabel("Gönderi Sayısı")
ax_w.grid(axis="y", linestyle="--", alpha=0.3)
st.pyplot(fig_w)

# -------------------- AYLIK ANALİZ --------------------
st.subheader("📅 Aylık Gönderi Analizi")

monthly = df.groupby("month").size()

# İlk ay anomalisi temizleme
if len(monthly) >= 2:
    if monthly.iloc[0] < monthly.iloc[1] * 0.5:
        monthly = monthly.iloc[1:]

st.dataframe(monthly.rename("Gönderi Sayısı").reset_index())

fig_m, ax_m = plt.subplots(figsize=(9, 4))
monthly.plot(marker="o", ax=ax_m)
ax_m.set_ylabel("Gönderi Sayısı")
ax_m.grid(True, linestyle="--", alpha=0.3)
st.pyplot(fig_m)

# -------------------- EXPORT --------------------
st.subheader("📁 Temizlenmiş Veri")

csv = df.to_csv(index=False).encode("utf-8")
st.download_button(
    "CSV indir",
    csv,
    "instagram_analiz.csv",
    "text/csv"
)
