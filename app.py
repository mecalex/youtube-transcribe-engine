import streamlit as st
import os
import re
from yt_dlp import YoutubeDL
from faster_whisper import WhisperModel

def saniye_to_srt_zaman(saniye):
    saat = int(saniye // 3600)
    dakika = int((saniye % 3600) // 60)
    sn = int(saniye % 60)
    milisaniye = int((saniye - int(saniye)) * 1000)
    return f"{saat:02d}:{dakika:02d}:{sn:02d},{milisaniye:03d}"

def guvenli_dosya_adi(isim):
    return re.sub(r'[\\/*?:"<>|]', "", isim)

st.set_page_config(page_title="Transcription Engine", page_icon="⚙️", layout="centered")

# CSS kısmı aynı...
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
    .stTextInput>div>div>input {
        background-color: #242b3d !important;
        color: #f1f5f9 !important;
        border: 1px solid #334155 !important;
        border-radius: 6px !important;
        padding: 12px 16px !important;
        font-size: 0.95rem !important;
        transition: all 0.2s ease;
    }
    .stTextInput>div>div>input:focus {
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
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="brand-header">transcribe.engine</div>', unsafe_allow_html=True)
st.markdown('<div class="brand-sub">Yapay zekâ destekli profesyonel ses deşifre ve altyazı servis istasyonu.</div>', unsafe_allow_html=True)
st.markdown('<div class="premium-ad-placement">— Sponsored Advertisement —</div>', unsafe_allow_html=True)

video_url = st.text_input("YOUTUBE URL", placeholder="YouTube video bağlantısını buraya girin...", label_visibility="collapsed")

if st.button("Çözümlemeyi Başlat"):
    if not video_url:
        st.warning("İşlem için geçerli bir video bağlantısı tanımlanmadı.")
    else:
        gecici_ses = "web_gecici_audio"
        cookie_path = os.path.join(os.getcwd(), 'cookies.txt')
        
        ydl_opts = {
            'outtmpl': gecici_ses,
            'js_runtimes': {'node': {}},
            'cookiefile': cookie_path if os.path.exists(cookie_path) else None,
            # ÇÖZÜM 1: Sadece en iyi audio'yu çek, fallback olarak herhangi bir şey al
            'format': 'bestaudio/best',
            # ÇÖZÜM 2: Format bulunamazsa hata vermek yerine varsayılan davranışa dön
            'ignoreerrors': True,
            # ÇÖZÜM 3: FFmpeg ile sadece audio extraction yap
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '128', 
            }],
            'quiet': True,
            'no_warnings': True,
            # ÇÖZÜM 4: Sadece metadata çek, sonra indir (daha stabil)
            'noplaylist': True,
            'restrictfilenames': True,
        }
        
        try:
            with st.spinner("Kaynak ayrıştırılıyor..."):
                with YoutubeDL(ydl_opts) as ydl:
                    info_dict = ydl.extract_info(video_url, download=True)
                    
                    # Eğer extract_info None dönerse (hata durumunda)
                    if info_dict is None:
                        raise Exception("Video bilgisi alınamadı. Lütfen URL'yi kontrol edin.")
                    
                    video_baslik = info_dict.get('title', 'transkript_output')
            
            # Kontrol: Dosya gerçekten oluştu mu?
            audio_path = gecici_ses + ".mp3"
            if not os.path.exists(audio_path):
                # Bazen dosya adı farklı olabilir, kontrol et
                possible_files = [f for f in os.listdir('.') if f.startswith(gecici_ses)]
                if possible_files:
                    audio_path = possible_files[0]
                else:
                    raise Exception("Ses dosyası oluşturulamadı. Format hatası devam ediyor olabilir.")
            
            guvenli_baslik = guvenli_dosya_adi(video_baslik)
            
            with st.spinner("Metinleştirme motoru çalışıyor..."):
                model = WhisperModel("tiny", device="cpu", compute_type="int8")
                segments, info = model.transcribe(audio_path, beam_size=3)
                
                srt_icerik = ""
                for i, segment in enumerate(segments, start=1):
                    start_time = saniye_to_srt_zaman(segment.start)
                    end_time = saniye_to_srt_zaman(segment.end)
                    srt_icerik += f"{i}\n{start_time} --> {end_time}\n{segment.text.strip()}\n\n"
            
            st.markdown(f"<p style='color: #cbd5e1; font-size: 0.9rem; font-weight: 500; text-align: center; margin-top: 15px;'>İşlem tamamlandı. Analiz Dili: {info.language.upper()}</p>", unsafe_allow_html=True)
            
            st.download_button(
                label="Dosyayı İndir (.SRT)",
                data=srt_icerik.encode('utf-8'),
                file_name=f"{guvenli_baslik}.srt",
                mime="text/plain"
            )
            
        except Exception as e:
            error_msg = str(e)
            # Kullanıcıya teknik detay gösterme, genel mesaj ver
            if "Requested format is not available" in error_msg:
                st.error("Video formatı desteklenmiyor. Lütfen başka bir video deneyin veya cookies.txt dosyası ekleyin.")
            elif "Sign in to confirm you're not a bot" in error_msg:
                st.error("YouTube bot koruması aktif. cookies.txt dosyası gerekiyor.")
            else:
                st.error(f"Beklenmeyen bir hata oluştu: {error_msg[:100]}...")
            
        finally:
            # Tüm geçici dosyaları temizle
            for ext in ['.mp3', '.m4a', '.webm']:
                temp_file = gecici_ses + ext
                if os.path.exists(temp_file):
                    os.remove(temp_file)

st.markdown('<div class="premium-ad-placement" style="margin-top: 50px;">— Sponsored Advertisement —</div>', unsafe_allow_html=True)
