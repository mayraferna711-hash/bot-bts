from playwright.sync_api import sync_playwright
import requests
import time
import random
from datetime import datetime
from colorama import Fore, Style, init

init(autoreset=True)

import os

TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

URLS = {
    "Colombia": "https://www.ticketmaster.co/event/bts-world-tour-2026",
    "Perú": "https://www.ticketmaster.pe/event/bts-world-tour-arirang"
}

# ⚙️ CONFIG
PAIS_MONITOREO = "Colombia"
INTERVALO_VIDA = 30

# 🎨 COLORES
colores = {
    "Colombia": Fore.YELLOW,
    "Perú": Fore.RED
}

# 🚨 ALERTA FUERTE (5 veces)
def alerta_boletos(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    for _ in range(5):
        requests.post(url, data={
            "chat_id": CHAT_ID,
            "text": "🚨🔥 BOLETOS DISPONIBLES 🔥🚨\n" + msg,
            "disable_notification": False
        })
        time.sleep(1)

# 🤖 ALERTA SUAVE (silenciosa)
def alerta_vida(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, data={
        "chat_id": CHAT_ID,
        "text": "🤖 " + msg,
        "disable_notification": True
    })

def check_tickets(page, url):
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=15000)
        page.wait_for_timeout(random.randint(800, 1500))

        content = page.content().lower()

        if "agotado" in content or "sold out" in content:
            return False

        posibles_botones = [
            "button:has-text('Comprar')",
            "button:has-text('Buy')",
            "a:has-text('Ver entradas')",
            "a:has-text('Find Tickets')"
        ]

        for selector in posibles_botones:
            botones = page.locator(selector)

            for i in range(botones.count()):
                boton = botones.nth(i)

                if boton.is_visible() and boton.is_enabled():
                    return True

    except Exception as e:
        print("Error en check:", e)

    return False


with sync_playwright() as p:
    browser = p.firefox.launch(headless=True)

    context = browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36",
        viewport={"width": 1280, "height": 800}
    )

    page = context.new_page()

    page.route("**/*", lambda route: route.abort()
        if route.request.resource_type in ["image", "stylesheet", "font", "media"]
        else route.continue_()
    )

    contadores = {pais: 0 for pais in URLS}
    estados = {pais: False for pais in URLS}

    while True:
        try:
            print("\n🔎", datetime.now().strftime("%H:%M:%S"))

            for pais, url in URLS.items():
                print(colores[pais] + f"🔎 Revisando Ticketmaster {pais}")

                hay_boletos = check_tickets(page, url)

                contadores[pais] += 1

                # 🤖 SOLO Colombia manda alerta de vida
                if pais == PAIS_MONITOREO and contadores[pais] >= INTERVALO_VIDA:
                    alerta_vida("Sigo revisando, NO HAY BOLETOS 🎟️")
                    contadores[pais] = 0

                if hay_boletos and not estados[pais]:
                    alerta_boletos(f"{pais}\n{url}")
                    print(colores[pais] + f"✅ DISPONIBLE {pais}")
                    estados[pais] = True
                    time.sleep(60)

                elif not hay_boletos:
                    print(colores[pais] + f"❌ Sin boletos {pais}")
                    estados[pais] = False

        except Exception as e:
            print("Error general:", e)

        time.sleep(random.randint(5, 8))
