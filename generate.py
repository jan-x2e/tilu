"""
Helsingin kouluruokalista — HTML-generaattori
=============================================
Hakee viikon ruokalistan ja generoi index.html-tiedoston.

Asennus:
    pip install playwright
    python -m playwright install chromium

Käyttö:
    python generate.py
"""

import re
from playwright.sync_api import sync_playwright
from datetime import datetime
from pathlib import Path

RAVINTOLA = "TikkurilaKO"
RAVINTOLA_NIMI = "Tikkurilan lukio"
BASE_URL = f"https://aromimenu.cgisaas.fi/VantaaAromieMenus/FI/Default/Vantti/{RAVINTOLA}/Page/Restaurant"
ODOTUSAIKA_MS = 8000

ALLERGEENIT = re.compile(r'\b(L|M|G|N|S|K|Veg|♥)\b')

PAIVA_FI = {
    "ma": "Maanantai",
    "ti": "Tiistai",
    "ke": "Keskiviikko",
    "to": "Torstai",
    "pe": "Perjantai",
}


def siisti_ruoka(teksti: str) -> str:
    return ALLERGEENIT.sub("", teksti).strip(" ,")


def hae_ruokalista():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        print(f"Haetaan: {BASE_URL} ...")
        page.goto(BASE_URL, timeout=30_000)
        page.wait_for_timeout(ODOTUSAIKA_MS)
        # Odotetaan sivun latautumista
        page.wait_for_timeout(ODOTUSAIKA_MS)

        # Klikataan "TÄMÄ VIIKKO" useammalla tavalla varmuuden vuoksi
        try:
            page.locator("text=TÄMÄ VIIKKO").first.click()
            page.wait_for_timeout(3000)
        except Exception:
            pass
        try:
            page.locator("text=Tämä viikko").first.click()
            page.wait_for_timeout(3000)
        except Exception:
            pass

        # Varmistetaan ettei olla enää TÄNÄÄN-näkymässä
        try:
            page.wait_for_selector("text=Maanantai", timeout=5000)
        except Exception:
            try:
                page.wait_for_selector("text=ma ", timeout=3000)
            except Exception:
                pass
        teksti = page.inner_text("body")
        browser.close()
    return jäsennä(teksti)


def jäsennä(teksti: str) -> dict:
    paivat = {}
    paiva_pattern = re.compile(
        r'(ma|ti|ke|to|pe)\s+\d{1,2}\.\d{1,2}\.\d{4}', re.IGNORECASE
    )
    rivit = teksti.splitlines()
    nykyinen_paiva = None
    nykyiset_ruoat = []
    kerataan = False

    for rivi in rivit:
        rivi = rivi.strip()
        if not rivi:
            continue
        if paiva_pattern.match(rivi):
            if nykyinen_paiva and nykyiset_ruoat:
                paivat[nykyinen_paiva] = nykyiset_ruoat
            nykyinen_paiva = rivi
            nykyiset_ruoat = []
            kerataan = True
            continue
        if rivi.startswith("Ajankohtaista") or rivi.startswith("©"):
            kerataan = False
        if not kerataan or not nykyinen_paiva:
            continue
        if rivi.lower() in ("lounas", "lounas."):
            continue
        osat = [o.strip() for o in rivi.split(",")]
        for osa in osat:
            puhdas = siisti_ruoka(osa)
            if puhdas and len(puhdas) > 2:
                nykyiset_ruoat.append(puhdas)

    if nykyinen_paiva and nykyiset_ruoat:
        paivat[nykyinen_paiva] = nykyiset_ruoat

    return paivat


def paiva_otsikko(paiva_str: str) -> tuple[str, str]:
    """Muuttaa 'ke 25.2.2026' -> ('Keskiviikko', '25.2.2026')"""
    osat = paiva_str.split()
    lyhenne = osat[0].lower()
    pvm = osat[1] if len(osat) > 1 else ""
    nimi = PAIVA_FI.get(lyhenne, paiva_str)
    return nimi, pvm


def generoi_html(paivat: dict) -> str:
    viikko = datetime.now().isocalendar().week
    nyt = datetime.now()
    paivitetty = f"{nyt.day}.{nyt.month}.{nyt.year} klo {nyt.strftime('%H:%M')}"

    # Rakennetaan päiväkortit
    kortit_html = ""
    for paiva_str, ruoat in paivat.items():
        nimi, pvm = paiva_otsikko(paiva_str)
        # Poistetaan duplikaatit
        naytettyt = list(dict.fromkeys(ruoat))

        ruoka_html = ""
        for r in naytettyt:
            ruoka_html += f'<li>{r}</li>\n'

        kortit_html += f"""
        <div class="kortti">
            <div class="paiva-otsikko">
                <span class="paiva-nimi">{nimi}</span>
                <span class="paiva-pvm">{pvm}</span>
            </div>
            <ul class="ruokalista">
                {ruoka_html}
            </ul>
        </div>
        """

    if not kortit_html:
        kortit_html = '<p class="ei-dataa">Ruokalistaa ei saatavilla.</p>'

    return f"""<!DOCTYPE html>
<html lang="fi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Ruokalista – {RAVINTOLA_NIMI}</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Fraunces:wght@400;600;700&family=DM+Sans:wght@400;500&display=swap" rel="stylesheet">
    <style>
        *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

        :root {{
            --ruutu: #1a1a2e;
            --pinta: #16213e;
            --kortti: #0f3460;
            --korostus: #e94560;
            --teksti: #eaeaea;
            --muted: #8892a4;
            --radius: 16px;
        }}

        body {{
            background: var(--ruutu);
            color: var(--teksti);
            font-family: 'DM Sans', sans-serif;
            min-height: 100vh;
            padding: 2rem 1rem 4rem;
        }}

        header {{
            text-align: center;
            margin-bottom: 3rem;
        }}

        header h1 {{
            font-family: 'Fraunces', serif;
            font-size: clamp(1.8rem, 5vw, 3rem);
            font-weight: 700;
            line-height: 1.1;
            color: #fff;
        }}

        header h1 span {{
            color: var(--korostus);
        }}

        .alaotsikko {{
            margin-top: 0.5rem;
            color: var(--muted);
            font-size: 0.95rem;
        }}

        .viikko-badge {{
            display: inline-block;
            margin-top: 1rem;
            background: var(--kortti);
            border: 1px solid var(--korostus);
            color: var(--korostus);
            padding: 0.3rem 1rem;
            border-radius: 100px;
            font-size: 0.85rem;
            font-weight: 500;
            letter-spacing: 0.05em;
            text-transform: uppercase;
        }}

        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
            gap: 1.25rem;
            max-width: 1200px;
            margin: 0 auto;
        }}

        .kortti {{
            background: var(--pinta);
            border: 1px solid rgba(255,255,255,0.07);
            border-radius: var(--radius);
            padding: 1.5rem;
            position: relative;
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }}

        .kortti:hover {{
            transform: translateY(-3px);
            box-shadow: 0 12px 30px rgba(0,0,0,0.3);
        }}

        .paiva-otsikko {{
            display: flex;
            align-items: baseline;
            justify-content: space-between;
            margin-bottom: 1rem;
            padding-bottom: 0.75rem;
            border-bottom: 1px solid rgba(255,255,255,0.08);
        }}

        .paiva-nimi {{
            font-family: 'Fraunces', serif;
            font-size: 1.3rem;
            font-weight: 600;
        }}

        .paiva-pvm {{
            font-size: 0.8rem;
            color: var(--muted);
        }}

        .ruokalista {{
            list-style: none;
            display: flex;
            flex-direction: column;
            gap: 0.5rem;
        }}

        .ruokalista li {{
            font-size: 0.9rem;
            color: var(--teksti);
            padding-left: 1rem;
            position: relative;
            line-height: 1.4;
        }}

        .ruokalista li::before {{
            content: '–';
            position: absolute;
            left: 0;
            color: var(--korostus);
        }}

        footer {{
            text-align: center;
            margin-top: 3rem;
            color: var(--muted);
            font-size: 0.8rem;
        }}

        footer a {{
            color: var(--korostus);
            text-decoration: none;
        }}

        .ei-dataa {{
            color: var(--muted);
            text-align: center;
            grid-column: 1/-1;
            padding: 3rem;
        }}

        @media (max-width: 600px) {{
            .grid {{ grid-template-columns: 1fr; }}
        }}
    </style>
</head>
<body>
    <header>
        <h1>{RAVINTOLA_NIMI.split(",")[0]}<span>,</span><br>{RAVINTOLA_NIMI.split(",")[1].strip() if "," in RAVINTOLA_NIMI else ""}</h1>
        <p class="alaotsikko">Palvelukeskus Helsinki</p>
        <div class="viikko-badge">Viikko {viikko}</div>
    </header>

    <main class="grid">
        {kortit_html}
    </main>

    <footer>
        <p>Päivitetty {paivitetty} &nbsp;·&nbsp; <a href="{BASE_URL}" target="_blank">Lähde: aromi.hel.fi</a></p>
    </footer>
</body>
</html>"""


if __name__ == "__main__":
    paivat = hae_ruokalista()

    html = generoi_html(paivat)
    out = Path("index.html")
    out.write_text(html, encoding="utf-8")
    print(f"✅ Generoitu: {out.resolve()}")
    print(f"   {len(paivat)} päivää löydetty")
