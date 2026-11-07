import streamlit as st
import os
import re
import requests
import json
import xml.etree.ElementTree as ET

def saniye_to_srt_zaman(saniye):
    saat = int(saniye // 3600)
    dakika = int((saniye % 3600) // 60)
    sn = int(saniye % 60)
    milisaniye = int((saniye - int(saniye)) * 1000)
    return f"{saat:02d}:{dakika:02d}:{sn:02d},{milisaniye:03d}"

def guvenli_dosya_adi(isim):
    return re.sub(r'[\\/*?:"<>|]', "", isim)

def youtube_id_bul(url):
    pattern = r'(?:v=|\/v\/|embed\/|youtu\.be\/|\/shorts\/|^)([a-zA-Z0-9_-]{11})'
    match = re.search(pattern, url)
    return match.group(1) if match else None

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
        video_id = youtube_id_bul(video_url)
        if not video_id:
            st.error("Geçerli bir YouTube Video ID'si tespit edilemedi.")
        else:
            try:
                with st.spinner("Yapay zekâ resmi transkript veri kanallarına sızıyor..."):
                    api_url = f"https://youtube.com{video_id}"
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                        'Accept-Language': 'tr,tr-TR;q=0.9,en-US;q=0.8,en;q=0.7'
                    }
                    
                    response = requests.get(api_url, headers=headers, timeout=15)
                    html_data = response.text
                    
                    baslik_match = re.search(r'<title>(.*?)</title>', html_data)
                    video_baslik = baslik_match.group(1).replace("- YouTube", "").strip() if baslik_match else "transkript_output"
                    guvenli_baslik = guvenli_dosya_adi(video_baslik)
                    
                    captions_match = re.search(r'"playerCaptionsTracklistRenderer":\s*({.*?})', html_data)
                    
                    if not captions_match:
                        st.error("Bu videoya ait herhangi bir resmi transkript veya altyazı verisi bulunamadı.")
                    else:
                        captions_json = json.loads(captions_match.group(1))
                        caption_tracks = captions_json.get('captionTracks', [])
                        
                        target_track = None
                        for track in caption_tracks:
                            if track.get('languageCode') == 'tr':
                                target_track = track
                                break
                        if not target_track:
                            for track in caption_tracks:
                                if track.get('languageCode') == 'en':
                                    target_track = track
                                    break
                        if not target_track and caption_tracks:
                            target_track = caption_tracks[0]
                            
                        if not target_track:
                            st.error("Transkript veri tüneli oluşturulamadı.")
                        else:
                            base_sub_url = target_track.get('baseUrl')
                            if "&fmt=" not in base_sub_url:
                                base_sub_url += "&fmt=srv1"
                                
                            sub_response = requests.get(base_sub_url, headers=headers, timeout=15)
                            xml_data = sub_response.text
                            
                            srt_icerik = ""
                            root = ET.fromstring(xml_data.encode('utf-8'))
                            for i, text_node in enumerate(root.findall('text'), start=1):
                                start = float(text_node.attrib.get('start', 0))
                                dur = float(text_node.attrib.get('dur', 0))
                                end = start + dur
                                
                                start_time = saniye_to_srt_zaman(start)
                                end_time = saniye_to_srt_zaman(end)
                                metin = text_node.text or ""
                                metin = metin.replace('&amp;', '&').replace('&quot;', '"').replace('&#39;', "'")
                                
                                srt_icerik += f"{i}\n{start_time} --> {end_time}\n{metin.strip()}\n\n"
                            
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
