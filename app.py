import streamlit as st
import os
import re
import tempfile
import yt_dlp
from yt_dlp import YoutubeDL
from faster_whisper import WhisperModel


def saniye_to_srt_zaman(saniye):
    """Saniye cinsinden zamanı SRT formatına çevirir."""
    saat = int(saniye // 3600)
    dakika = int((saniye % 3600) // 60)
    sn = int(saniye % 60)
    milisaniye = int((saniye - int(saniye)) * 1000)
    return f"{saat:02d}:{dakika:02d}:{sn:02d},{milisaniye:03d}"


def guvenli_dosya_adi(isim):
    """Dosya adından geçersiz karakterleri temizler."""
    return re.sub(r'[\\/*?:"<>|]', "", isim)


st.set_page_config(
    page_title="Transcription Engine",
    page_icon="⚙️",
    layout="centered"
)

# ============================================
# CSS STYLES
# ============================================
st.markdown("""
    <style>
    .stApp {
        background-color: #1a1f2c !important;
        font-family: -apple-system, system-ui, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }
    .brand-header {
        font-size: 1.6rem !important;
        font-weight: 600;
        color: #e2e8f0 !important;
        text-align: center;
        margin-top: 40px;
        margin-bottom: 4px;
        letter-spacing: -0.3px;
    }
    .brand-sub {
        color: #8da2bb;
        text-align: center;
        font-size: 0.9rem;
        margin-bottom: 40px;
    }
    .stTextInput > div > div > input {
        background-color: #242b3d !important;
        color: #f1f5f9 !important;
        border: 1px solid #334155 !important;
        border-radius: 6px !important;
        padding: 12px 16px !important;
        font-size: 0.95rem !important;
        transition: all 0.2s ease;
    }
    .stTextInput > div > div > input:focus {
        border-color: #64748b !important;
        box-shadow: 0 0 0 1px #64748b !important;
    }
    .premium-ad-placement {
        text-align: center;
        font-size: 0.75rem;
        color: #475569;
        margin: 25px 0;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    div.stButton > button:first-child {
        background-color: #f1f5f9 !important;
        color: #0f172a !important;
        font-weight: 500 !important;
        font-size: 0.9rem !important;
        padding: 11px 20px !important;
        border-radius: 6px !important;
        border: none !important;
        width: 100% !important;
        margin-top: 10px;
        transition: background-color 0.2s ease !important;
    }
    div.stButton > button:first-child:hover {
        background-color: #e2e8f0 !important;
    }
    div[data-testid="stDownloadButton"] > button {
        background-color: #242b3d !important;
        color: #f1f5f9 !important;
        font-weight: 500 !important;
        font-size: 0.9rem !important;
        border-radius: 6px !important;
        border: 1px solid #334155 !important;
        padding: 11px !important;
        width: 100% !important;
    }
    div[data-testid="stDownloadButton"] > button:hover {
        background-color: #2e374e !important;
        border-color: #475569 !important;
    }
    #MainMenu { visibility: hidden; }
    footer { visibility: hidden; }
    header { visibility: hidden; }
    </style>
""", unsafe_allow_html=True)

# ============================================
# BRANDING
# ============================================
st.markdown('<div class="brand-header">transcribe.engine</div>', unsafe_allow_html=True)
st.markdown('<div class="brand-sub">Yapay zeka destekli profesyonel ses deşifre ve altyazi servis istasyonu.</div>', unsafe_allow_html=True)
st.markdown('<div class="premium-ad-placement">— Sponsored Advertisement —</div>', unsafe_allow_html=True)

# ============================================
# INPUT
# ============================================
video_url = st.text_input(
    "YOUTUBE URL",
    placeholder="YouTube video baglantisini buraya girin...",
    label_visibility="collapsed"
)

if st.button("Cozumlemeyi Baslat"):
    if not video_url:
        st.warning("Islem icin gecerli bir video baglantisi tanimlanmadi.")
    else:
        gecici_ses = "web_gecici_audio"

        # ============================================
        # YT-DLP AYARLARI — GÜNCEL VE GÜVENİLİR
        # ============================================
        ydl_opts = {
            'outtmpl': gecici_ses + '.%(ext)s',
            'format': 'bestaudio[ext=m4a]/bestaudio[ext=webm]/bestaudio/best',
            'noplaylist': True,
            'quiet': False,
            'no_warnings': False,
            'extractor_args': {
                'youtube': {
                    'player_client': ['web', 'android', 'ios'],
                }
            },
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }

        try:
            # ===== 1. VIDEO BILGISINI AL =====
            with st.spinner("Kaynak ayristiriliyor..."):
                with YoutubeDL(ydl_opts) as ydl:
                    info_dict = ydl.extract_info(video_url, download=True)
                    video_baslik = info_dict.get('title', 'transkript_output')

            # ===== 2. SES DOSYASINI BUL =====
            audio_path = None
            for ext in ['.mp3', '.m4a', '.webm']:
                candidate = gecici_ses + ext
                if os.path.exists(candidate):
                    audio_path = candidate
                    break

            if not audio_path:
                # Dosya ismini tam olarak bulmak icin ydl_opts'a outtmpl yazdiralim
                remaining_files = [f for f in os.listdir('.') if f.startswith(gecici_ses)]
                raise Exception(
                    f"Ses dosyasi bulunamadi! Kalan dosyalar: {remaining_files}"
                )

            # ===== 3. WHISPER TRANSCRIPTION =====
            guvenli_baslik = guvenli_dosya_adi(video_baslik)

            with st.spinner("Metinlestirme motoru calisiyor..."):
                model = WhisperModel("tiny", device="cpu", compute_type="int8")
                segments, info = model.transcribe(audio_path, beam_size=3)

                # ===== 4. SRT OLUŞTUR =====
                srt_icerik = ""
                for i, segment in enumerate(segments, start=1):
                    start_time = saniye_to_srt_zaman(segment.start)
                    end_time = saniye_to_srt_zaman(segment.end)
                    srt_icerik += f"{i}\n{start_time} --> {end_time}\n{segment.text.strip()}\n\n"

            # ===== 5. BASARI MESAJI =====
            st.markdown(
                f"<p style='color: #cbd5e1; font-size: 0.9rem; font-weight: 500; "
                f"text-align: center; margin-top: 15px;'>"
                f"Islem tamamlandi. Analiz Dili: {info.language.upper()} "
                f"(guven: {info.probability:.1%})</p>",
                unsafe_allow_html=True
            )

            # ===== 6. INDIRME BUTONU =====
            st.download_button(
                label="Dosyayi Indir (.SRT)",
                data=srt_icerik.encode('utf-8'),
                file_name=f"{guvenli_baslik}.srt",
                mime="text/plain"
            )

        except Exception as e:
            st.error(f"Sistem raporu hatasi:\n\n{e}")
            import traceback
            st.code(traceback.format_exc())

        finally:
            # ===== 7. TEMIZLIK =====
            for ext in ['.mp3', '.m4a', '.webm', '.ts']:
                temp_file = gecici_ses + ext
                if os.path.exists(temp_file):
                    os.remove(temp_file)

# ============================================
# ALT REKLAM
# ============================================
st.markdown('<div class="premium-ad-placement" style="margin-top: 50px;">— Sponsored Advertisement —</div>', unsafe_allow_html=True)

# ============================================
# TEŞHİS BÖLÜMÜ
# ============================================
st.divider()
with st.expander("🔧 TEŞHİS: yt-dlp sürümü ve format listesi"):
    st.write(f"**yt-dlp sürümü:** `{yt_dlp.version.__version__}`")
    test_url = st.text_input("Test URL", value="https://www.youtube.com/watch?v=qdrjjjWwnyM")
    if st.button("Formatları Sorgula"):
        try:
            with YoutubeDL({'quiet': True, 'simulate': True, 'playlist_items': '1'}) as y:
                i = y.extract_info(test_url, download=False)
                fmts = i.get('formats', [])
                st.success(f"Toplam {len(fmts)} format bulundu.")
                for f in fmts[-25:]:
                    st.code(f"{f.get('format_id')} | ext={f.get('ext')} | acodec={f.get('acodec')} | vcodec={f.get('vcodec')}")
        except Exception as ex:
            st.error(f"Sorgu hatasi: {ex}")
