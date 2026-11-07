import streamlit as st
import os
import re
from yt_dlp import YoutubeDL

def saniye_to_srt_zaman(saniye):
    saat = int(saniye // 3600)
    dakika = int((saniye % 3600) // 60)
    sn = int(saniye % 60)
    milisaniye = int((saniye - int(saniye)) * 1000)
    return f"{saat:02d}:{dakika:02d}:{sn:02d},{milisaniye:03d}"

def guvenli_dosya_adi(isim):
    return re.sub(r'[\\/*?:"<>|]', "", isim)

st.set_page_config(page_title="Transcription Engine", page_icon="⚙️", layout="centered")

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
        cookie_path = os.path.join(os.getcwd(), 'cookies.txt')
        
        ydl_opts = {
            # IP engeline takılan ağır medya indirme süreçleri tamamen pas geçiliyor
            'skip_download': True,
            'writesubtitles': True,
            'writeautomaticsub': True,
            'subtitleslangs': ['tr', 'en', 'all'], 
            'js_runtimes': {'node': {}},
            'cookiefile': cookie_path if os.path.exists(cookie_path) else None,
            'quiet': True,
        }
        try:
            with st.spinner("Yapay zekâ transkript verilerini YouTube tünellerinden çekiyor..."):
                with YoutubeDL(ydl_opts) as ydl:
                    info_dict = ydl.extract_info(video_url, download=False)
                    video_baslik = info_dict.get('title', 'transkript_output')
                    
                    subtitles = info_dict.get('subtitles', {})
                    automatic_captions = info_dict.get('automatic_captions', {})
            
            guvenli_baslik = guvenli_dosya_adi(video_baslik)
            
            altyazi_listesi = None
            if 'tr' in subtitles:
                altyazi_listesi = subtitles['tr']
            elif 'tr' in automatic_captions:
                altyazi_listesi = automatic_captions['tr']
            elif 'en' in subtitles:
                altyazi_listesi = subtitles['en']
            elif 'en' in automatic_captions:
                altyazi_listesi = automatic_captions['en']
            elif len(subtitles) > 0:
                altyazi_listesi = list(subtitles.values())[0]
            elif len(automatic_captions) > 0:
                altyazi_listesi = list(automatic_captions.values())[0]
                
            if altyazi_listesi is None:
                st.error("Bu videoya ait herhangi bir resmi transkript veya altyazı verisi bulunamadı.")
            else:
                srv1_url = None
                if isinstance(altyazi_listesi, list):
                    for sub in altyazi_listesi:
                        if sub.get('ext') == 'srv1':
                            srv1_url = sub.get('url')
                            break
                    if not srv1_url and altyazi_listesi:
                        srv1_url = altyazi_listesi[0].get('url')
                else:
                    srv1_url = altyazi_listesi.get('url')
                    
                if not srv1_url:
                    st.error("Transkript veri tüneli oluşturulamadı.")
                else:
                    import urllib.request
                    import xml.etree.ElementTree as ET
                    
                    req = urllib.request.Request(srv1_url, headers={'User-Agent': 'Mozilla/5.0'})
                    xml_data = urllib.request.urlopen(req).read().decode('utf-8')
                    
                    srt_icerik = ""
                    try:
                        root = ET.fromstring(xml_data)
                        for i, text_node in enumerate(root.findall('text'), start=1):
                            start = float(text_node.attrib.get('start', 0))
                            dur = float(text_node.attrib.get('dur', 0))
                            end = start + dur
                            
                            start_time = saniye_to_srt_zaman(start)
                            end_time = saniye_to_srt_zaman(end)
                            metin = text_node.text or ""
                            metin = metin.replace('&amp;', '&').replace('&quot;', '"').replace('&#39;', "'")
                            
                            srt_icerik += f"{i}\n{start_time} --> {end_time}\n{metin.strip()}\n\n"
                    except Exception:
                        srt_icerik = xml_data
                    
                    st.markdown("<p style='color: #cbd5e1; font-size: 0.9rem; font-weight: 500; text-align: center; margin-top: 15px;'>İşlem başarıyla tamamlandı!</p>", unsafe_allow_html=True)
                    
                    st.download_button(
                        label="Dosyayı İndir (.SRT)",
                        data=srt_icerik.encode('utf-8'),
                        file_name=f"{guvenli_baslik}.srt",
                        mime="text/plain"
                    )
            
        except Exception as e:
            st.error(f"Sistem raporu hatası: {e}")

st.markdown('<div class="premium-ad-placement" style="margin-top: 50px;">— Sponsored Advertisement —</div>', unsafe_allow_html=True)
