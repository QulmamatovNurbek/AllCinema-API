from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import requests
from bs4 import BeautifulSoup

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/get_video")
def get_video_link(url: str):
    if url.lower().endswith(".mp4"):
        return {"so'ralgan_link": url, "topilgan_videolar": {"Asosiy": url}, "holat": "MP4 fayl"}
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers)
        if response.status_code != 200: raise HTTPException(status_code=400, detail="Saytga kirib bo'lmadi")
        soup = BeautifulSoup(response.text, "html.parser")
        video_links = {}

        buttons = soup.find_all("button", class_="fs-player__tab")
        for btn in buttons:
            sifat, link = btn.get("data-name"), btn.get("data-url")
            if sifat and link: video_links[sifat] = link
            
        if video_links: return {"so'ralgan_link": url, "topilgan_videolar": video_links, "holat": "Muvaffaqiyatli!"}
        
        video_tag = soup.find("video")
        if video_tag and video_tag.get("src"): return {"topilgan_videolar": {"Standart": video_tag.get("src")}, "holat": "Oddiy video"}
        
        iframe_tag = soup.find("iframe")
        if iframe_tag and iframe_tag.get("src"): return {"topilgan_videolar": {"Iframe": iframe_tag.get("src")}, "holat": "Iframe"}
        
        return {"xato": "Video link topilmadi."}
    except Exception as e:
        return {"xato": str(e)}

@app.get("/movies")
def get_movies(query: str = "tarjima", type: str = "search"):
    try:
        # Janrlar lug'ati (saytdagi ruscha URL larga to'g'rilash uchun)
        janrlar = {"jangari": "боевик", "komediya": "комедия", "qorqinchli": "ужасы", "fantastika": "фантастика", "drama": "драма", "sarguzasht": "приключения"}
        
        if type == "genre":
            q = janrlar.get(query.lower(), query)
            url = f"https://asilmedia.org/xfsearch/genre/{q}/"
        elif type == "year":
            url = f"https://asilmedia.org/xfsearch/year/{query}/"
        else:
            url = f"https://asilmedia.org/index.php?do=search&subaction=search&story={query}"

        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers)
        if response.status_code != 200: raise HTTPException(status_code=400, detail="Ulanib bo'lmadi")
        
        soup = BeautifulSoup(response.text, "html.parser")
        natijalar = []
        cards = soup.find_all(['article', 'div'], class_=lambda c: c and ('card' in c or 'short' in c))
        
        for card in cards:
            link_tag = card.find('a')
            if not link_tag or not link_tag.get('href') or '.html' not in link_tag.get('href'): continue
            kino_linki = link_tag.get('href')
            title_tag = card.find(['h2', 'h3'])
            kino_nomi = title_tag.text.strip() if title_tag else ""
            img_tag = card.find('img')
            rasm_linki = img_tag.get('src') or img_tag.get('data-src') if img_tag else "Rasm topilmadi"
            if rasm_linki.startswith("/"): rasm_linki = "https://asilmedia.org" + rasm_linki
            if not kino_nomi and img_tag and img_tag.get('alt'): kino_nomi = img_tag.get('alt')
            meta_tag = card.find('div', class_=lambda c: c and 'meta' in c)
            qoshimcha = meta_tag.text.strip() if meta_tag else "Kino haqida ma'lumot"
            
            if kino_nomi and kino_linki:
                natijalar.append({"nomi": kino_nomi, "rasmi": rasm_linki, "qoshimcha": qoshimcha, "linki": kino_linki})

        if natijalar: return {"kinolar": natijalar, "holat": "Topildi!"}
        else: return {"xato": "Hech narsa topilmadi."}
    except Exception as e:
        return {"xato": str(e)}
