from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import requests
from bs4 import BeautifulSoup

app = FastAPI()

# Frontend saytimiz API ga ulanishi uchun ruxsat beramiz
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/get_video")
def get_video_link(url: str):
    # 1. Agar to'g'ridan-to'g'ri MP4 berilsa
    if url.lower().endswith(".mp4"):
        return {
            "so'ralgan_link": url,
            "topilgan_video": {"Asosiy": url},
            "holat": "Bu tayyor MP4 fayl ekan! 🍿"
        }

    try:
        # 2. Saytga kirib HTML'ni o'qish
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers)
        
        if response.status_code != 200:
            raise HTTPException(status_code=400, detail="Saytga kirib bo'lmadi")

        soup = BeautifulSoup(response.text, "html.parser")
        video_links = {}

        # 3. Asilmedia siri: `fs-player__tab` klassiga ega tugmalarni qidirish
        buttons = soup.find_all("button", class_="fs-player__tab")
        
        for btn in buttons:
            sifat = btn.get("data-name") # 480p, 720p degan yozuvni olamiz
            link = btn.get("data-url")   # mp4 ssilkani olamiz
            if sifat and link:
                video_links[sifat] = link

        # 4. Agar tugmalar ichidan topilsa, natijani qaytarish
        if video_links:
            return {
                "so'ralgan_link": url,
                "topilgan_videolar": video_links,
                "holat": "Muvaffaqiyatli! Barcha sifatdagi videolar topildi 🎬"
            }
        
        # 5. Ehtiyot shart: Agar bu Asilmedia bo'lmasa, oddiy <video> larni qidirib ko'ramiz
        video_tag = soup.find("video")
        if video_tag and video_tag.get("src"):
            return {"topilgan_videolar": {"Standart": video_tag.get("src")}, "holat": "Oddiy video topildi"}

        iframe_tag = soup.find("iframe")
        if iframe_tag and iframe_tag.get("src"):
            return {"topilgan_videolar": {"Iframe": iframe_tag.get("src")}, "holat": "Iframe pleyer topildi"}

        return {"xato": "Bu sahifadan aniq video link topilmadi."}

    except Exception as e:
        return {"xato": f"Kutilmagan xatolik: {str(e)}"}
    

@app.get("/search")
def search_movie(query: str):
    try:
        url = f"https://asilmedia.org/index.php?do=search&subaction=search&story={query}"
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers)
        
        if response.status_code != 200:
            raise HTTPException(status_code=400, detail="Qidiruv tizimiga ulanib bo'lmadi")

        soup = BeautifulSoup(response.text, "html.parser")
        natijalar = []

        # 1. Kinolar qutichasini qidiramiz
        cards = soup.find_all(['article', 'div'], class_=lambda c: c and ('card' in c or 'short' in c))
        
        for card in cards:
            link_tag = card.find('a')
            if not link_tag or not link_tag.get('href') or '.html' not in link_tag.get('href'):
                continue
            
            kino_linki = link_tag.get('href')
            
            title_tag = card.find(['h2', 'h3'])
            kino_nomi = title_tag.text.strip() if title_tag else ""
            
            img_tag = card.find('img')
            rasm_linki = "Rasm topilmadi"
            if img_tag:
                rasm_linki = img_tag.get('src') or img_tag.get('data-src') or "Rasm topilmadi"
                if rasm_linki.startswith("/"):
                    rasm_linki = "https://asilmedia.org" + rasm_linki
                if not kino_nomi and img_tag.get('alt'):
                    kino_nomi = img_tag.get('alt')

            meta_tag = card.find('div', class_=lambda c: c and 'meta' in c)
            qoshimcha = meta_tag.text.strip() if meta_tag else "Ma'lumot yo'q"

            if kino_nomi and kino_linki:
                natijalar.append({
                    "nomi": kino_nomi,
                    "rasmi": rasm_linki,
                    "qoshimcha": qoshimcha,
                    "linki": kino_linki
                })

        if natijalar:
            return {
                "qidiruv_sozi": query,
                "topilgan_kinolar_soni": len(natijalar),
                "kinolar": natijalar,
                "holat": "Muvaffaqiyatli topildi! 🔎"
            }
        else:
            return {"xato": f"'{query}' bo'yicha hech qanday kino topilmadi."}

    except Exception as e:
        return {"xato": f"Kutilmagan xatolik yuz berdi: {str(e)}"}
