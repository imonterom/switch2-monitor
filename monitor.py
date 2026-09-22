import hashlib
import html
import json
import os
import re
from pathlib import Path
from urllib.parse import parse_qs, unquote, urljoin, urlparse

import requests
from bs4 import BeautifulSoup

STANDARD_LIMIT = 550_000
BUNDLE_LIMIT = 600_000
STATE_FILE = Path("state.json")

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "").strip()
ZELDA_GROUP_ID = "-5304374891"
TEST_NOTIFICATION = os.environ.get("TEST_NOTIFICATION", "false").lower() in {"1", "true", "yes"}

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/128.0 Safari/537.36"
    ),
    "Accept-Language": "es-CL,es;q=0.9,en;q=0.8",
}

# Fuentes concretas y confiables. Si una tienda cambia la URL, basta con actualizar esta lista.
SOURCES = [
    {
        "id": "bestmart_standard",
        "store": "Bestmart",
        "title": "Nintendo Switch 2",
        "kind": "standard",
        "url": "https://bestmart.cl/collections/consolas-nintendo-switch/products/consola-nintendo-switch-2-negro",
    },
    {
        "id": "bestmart_mario_bundle",
        "store": "Bestmart",
        "title": "Nintendo Switch 2 + Mario Kart World",
        "kind": "bundle",
        "url": "https://bestmart.cl/collections/nintendo/products/consola-nintendo-switch-2-bundle-mario-kart-world",
    },
    {
        "id": "bestmart_choose_bundle",
        "store": "Bestmart",
        "title": "Nintendo Switch 2 - Elige tu juego",
        "kind": "bundle",
        "url": "https://bestmart.cl/collections/recien-llegados/products/consola-nintendo-switch-2-bundle-elige-tu-juego",
    },
    {
        "id": "weplay_standard",
        "store": "WePlay",
        "title": "Nintendo Switch 2",
        "kind": "standard",
        "url": "https://www.weplay.cl/consola-nintendo-switch-2.html",
    },
    {
        "id": "weplay_mario_bundle",
        "store": "WePlay",
        "title": "Nintendo Switch 2 + Mario Kart World",
        "kind": "bundle",
        "url": "https://www.weplay.cl/consola-nintendo-switch-2-mario-kart-world.html",
    },
    {
        "id": "weplay_choose_bundle",
        "store": "WePlay",
        "title": "Nintendo Switch 2 - Choose Your Game Bundle",
        "kind": "bundle",
        "url": "https://www.weplay.cl/consola-nintendo-switch-2-choose-your-game-bundle.html",
    },
    {
        "id": "falabella_standard",
        "store": "Falabella",
        "title": "Nintendo Switch 2",
        "kind": "standard",
        "url": "https://www.falabella.com/falabella-cl/product/17448346/Nintendo-Switch-2",
        "required_text": "vendido por falabella",
    },
    {
        "id": "falabella_choose_bundle",
        "store": "Falabella",
        "title": "Nintendo Switch 2 - Bundle",
        "kind": "bundle",
        "url": "https://www.falabella.com/falabella-cl/product/80774668/consola-nintendo-switch-2-bund-choose",
        "required_text": "vendido por falabella",
    },
    {
        "id": "mercadolibre_nintendo_official",
        "store": "Mercado Libre - Tienda Oficial Nintendo",
        "title": "Nintendo Switch 2",
        "kind": "standard",
        "url": "https://www.mercadolibre.cl/nintendo-switch-2-system/p/MLC51986500",
        "required_text": "tienda oficial",
    },
    {
        "id": "pcfactory_switch2_56565",
        "store": "PC Factory (seguimiento TecnoGangas)",
        "title": "Nintendo Switch 2",
        "kind": "standard",
        "url": "https://tecnogangas.cl/producto/35789-nintendo-switch-2-256gb-12gb-ram-7-9-tela-lcd-fhd-usb-c-wi-fi-5220-mah-bluetooth-4-1",
    },
    {
        "id": "pcfactory_switch2_us_56075",
        "store": "PC Factory (seguimiento TecnoGangas)",
        "title": "Nintendo Switch 2 US",
        "kind": "standard",
        "url": "https://tecnogangas.cl/producto/39223-nintendo-switch-2-formato-us-256gb-12gb-ram-7-9-tela-lcd-fhd-usb-c-wi-fi-5220-mah-bluetooth-4-1",
    },
]

SOLOTODO_PRODUCTS = [
    {
        "id": "solotodo_standard",
        "title": "Nintendo Switch 2",
        "kind": "standard",
        "url": "https://www.solotodo.cl/products/273115-nintendo-switch-2-black",
    },
    {
        "id": "solotodo_mario_bundle",
        "title": "Nintendo Switch 2 + Mario Kart World",
        "kind": "bundle",
        "url": "https://www.solotodo.cl/products/273116-nintendo-switch-2-black-mario-kart-world",
    },
    {
        "id": "solotodo_choose_bundle",
        "title": "Nintendo Switch 2 - Choose Your Game",
        "kind": "bundle",
        "url": "https://www.solotodo.cl/products/396411-nintendo-switch-2-black-choose-your-game",
    },
]

# Tiendas grandes que agregamos mediante SoloTodo. Las demás ya se siguen
# directamente en SOURCES para evitar alertas duplicadas.
SOLOTODO_STORES = ("Paris", "Ripley", "Lider", "Hites", "ABC")

ZELDA_SOURCES = [
    {
        "id": "zelda_bestmart",
        "store": "Bestmart",
        "title": "Nintendo Switch 2 - The Legend of Zelda 40.º Aniversario",
        "url": "https://bestmart.cl/collections/preventas-exclusivas-bestmart-chile/products/consola-nintendo-switch-2-the-legend-of-zelda-edicion-40-aniversario",
    },
    {
        "id": "zelda_weplay",
        "store": "WePlay",
        "title": "Nintendo Switch 2 - The Legend of Zelda 40TH Aniversario",
        "url": "https://www.weplay.cl/preventa-consola-switch-2-the-legend-of-zelda-40th-aniversario.html",
    },
    {
        "id": "zelda_mathogames",
        "store": "Mathogames",
        "title": "Nintendo Switch 2 - The Legend of Zelda 40TH Anniversary",
        "url": "https://www.mathogames.cl/consolas-switch-2/2538-preventa-dia-1-consola-nintendo-switch-2-the-legend-of-zelda-40th-anniversary.html",
    },
    {
        "id": "zelda_santogames",
        "store": "Santo Games",
        "title": "Nintendo Switch 2 - The Legend of Zelda 40.º Aniversario",
        "url": "https://www.santogames.cl/nintendo-switch-2-the-legend-of-zelda-40%C2%BA-aniversario",
    },
    {
        "id": "zelda_todojuegos",
        "store": "TodoJuegos",
        "title": "Nintendo Switch 2 - Zelda 40TH Aniversario",
        "url": "https://www.todojuegos.cl/Productos/NS2/Consola-Switch-2-Zelda-40th-Aniversario/",
    },
    {
        "id": "zelda_mercadolibre",
        "store": "Mercado Libre",
        "title": "Nintendo Switch 2 - The Legend of Zelda 40TH Anniversary Edition",
        "url": "https://www.mercadolibre.cl/nintendo-switch-2-the-legend-of-zelda-40th-anniversary-edition/p/MLC79375219",
    },
]

# Capa de descubrimiento para detectar nuevas fichas en retailers grandes.
ZELDA_DISCOVERY_PAGES = [
    ("Falabella", "https://www.falabella.com/falabella-cl/search?Ntt=nintendo%20switch%202%20zelda%2040"),
    ("Ripley", "https://simple.ripley.cl/search/nintendo%20switch%202%20zelda%2040"),
    ("Paris", "https://www.paris.cl/search?q=nintendo%20switch%202%20zelda%2040"),
    ("Lider", "https://www.lider.cl/catalogo/search?query=nintendo%20switch%202%20zelda%2040"),
    ("Hites", "https://www.hites.com/search?q=nintendo%20switch%202%20zelda%2040"),
    ("ABC", "https://www.abc.cl/search?q=nintendo%20switch%202%20zelda%2040"),
]

EXCLUDED_TERMS = (
    "preventa",
    "pre-venta",
    "preventa ",
    "preorder",
    "pre-order",
    "zelda",
    "reacondicionado",
    "reacondicionada",
    "usado",
    "usada",
)


def load_state():
    if not STATE_FILE.exists():
        return {}
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_state(state):
    STATE_FILE.write_text(
        json.dumps(state, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def format_clp(value):
    return "$" + f"{value:,}".replace(",", ".")


def send_telegram_to(chat_id, message):
    if not BOT_TOKEN or not chat_id:
        raise RuntimeError("Falta TELEGRAM_BOT_TOKEN o el chat_id de destino.")

    response = requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        json={
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "HTML",
            "disable_web_page_preview": False,
        },
        timeout=20,
    )
    response.raise_for_status()


def send_telegram(message):
    send_telegram_to(CHAT_ID, message)


def normalize_price(raw):
    if raw is None:
        return None

    digits = re.sub(r"\D", "", str(raw))
    if not digits:
        return None

    value = int(digits)
    if 450_000 <= value <= 1_200_000:
        return value
    return None


def walk_json_prices(node):
    values = []

    if isinstance(node, dict):
        for key, value in node.items():
            if key.lower() in {"price", "lowprice", "highprice"}:
                parsed = normalize_price(value)
                if parsed is not None:
                    values.append(parsed)
            values.extend(walk_json_prices(value))

    elif isinstance(node, list):
        for value in node:
            values.extend(walk_json_prices(value))

    return values


def extract_primary_prices(source, soup, text):
    # TecnoGangas muestra explícitamente "Oferta $X".
    if "tecnogangas.cl" in source["url"]:
        match = re.search(
            r"Oferta\s*(?:CLP\s*)?\$\s*([0-9]{1,3}(?:[.\s][0-9]{3})+)",
            text,
            flags=re.I,
        )
        if match:
            value = normalize_price(match.group(1))
            if value is not None:
                return [value]

    structured = []

    for selector in (
        'meta[property="product:price:amount"]',
        'meta[property="og:price:amount"]',
        'meta[itemprop="price"]',
    ):
        for meta in soup.select(selector):
            value = normalize_price(meta.get("content"))
            if value is not None:
                structured.append(value)

    for script in soup.find_all("script", attrs={"type": "application/ld+json"}):
        raw = script.string or script.get_text(strip=True)
        if not raw:
            continue

        try:
            data = json.loads(raw)
        except Exception:
            continue

        structured.extend(walk_json_prices(data))

    if structured:
        return sorted(set(structured))

    main = soup.find("main")
    scoped_text = " ".join(main.stripped_strings) if main else text
    prices = extract_prices(scoped_text)
    if prices:
        return prices

    return extract_prices(text)


def extract_prices(text):
    # Detecta formatos chilenos típicos: $569.990, CLP$ 569.990, etc.
    matches = re.findall(r"(?:CLP\s*)?\$\s*([0-9]{1,3}(?:[.\s][0-9]{3})+)", text, flags=re.I)
    values = []
    for raw in matches:
        try:
            value = int(re.sub(r"\D", "", raw))
        except ValueError:
            continue

        # Evita cuotas, accesorios y precios absurdos para una consola.
        if 450_000 <= value <= 1_200_000:
            values.append(value)

    return sorted(set(values))


def extract_direct_store_link(soup, fallback):
    for anchor in soup.find_all("a", href=True):
        label = " ".join(anchor.stripped_strings).lower()
        if "ir a la tienda" in label or "ver oferta tienda" in label:
            return requests.compat.urljoin(fallback, anchor["href"])
    return fallback


def fetch_source(source):
    response = requests.get(source["url"], headers=HEADERS, timeout=25)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    text = " ".join(soup.stripped_strings)
    text_lower = text.lower()

    # Protección contra ediciones/publicaciones que no interesan, mirando solo
    # el encabezado real del producto para no confundir recomendaciones secundarias.
    h1 = soup.find("h1")
    header_text = " ".join(h1.stripped_strings).lower() if h1 else source["title"].lower()
    source_identity = f"{source['title']} {source['url']} {header_text}".lower()
    if any(term in source_identity for term in EXCLUDED_TERMS):
        print(f"[SKIP] {source['store']}: producto excluido por nombre.")
        return None

    required = source.get("required_text")
    if required and required.lower() not in text_lower:
        print(f"[SKIP] {source['store']}: no se confirmó '{required}'.")
        return None

    # Casos claros de producto agotado.
    if "justo se agotó" in text_lower or "producto agotado" in text_lower:
        print(f"[SKIP] {source['store']}: producto agotado.")
        return None

    prices = extract_primary_prices(source, soup, text)
    if not prices:
        raise RuntimeError("No se encontró un precio de consola válido.")

    # En páginas de producto el menor valor plausible corresponde al precio efectivo/oferta,
    # mientras que los valores superiores suelen ser precio normal/referencia.
    price = min(prices)

    return {
        "price": price,
        "url": extract_direct_store_link(soup, source["url"]),
    }



def slugify(value):
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9]+", "_", value)
    return value.strip("_")


def normalize_solotodo_link(href, base_url):
    href = urljoin(base_url, href)
    parsed = urlparse(href)
    query = parse_qs(parsed.query)

    # SoloTodo usa algunos enlaces de redirección/afiliado. Extraemos la URL
    # final cuando viene explícita en el parámetro.
    for key in ("url", "dl"):
        if key in query and query[key]:
            target = unquote(query[key][0])
            if target.startswith("http://") or target.startswith("https://"):
                return target

    return href


def fetch_solotodo_offers(product):
    response = requests.get(product["url"], headers=HEADERS, timeout=25)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    offers = []

    for anchor in soup.find_all("a", href=True):
        label = " ".join(anchor.stripped_strings).strip()
        label_lower = label.lower()

        store = next(
            (name for name in SOLOTODO_STORES if label_lower.startswith(name.lower())),
            None,
        )
        if not store:
            continue

        prices = extract_prices(label)
        if not prices:
            continue

        price = min(prices)
        offers.append(
            {
                "id": f"{product['id']}_{slugify(store)}",
                "store": store,
                "title": product["title"],
                "kind": product["kind"],
                "price": price,
                "url": normalize_solotodo_link(anchor["href"], product["url"]),
            }
        )

    return offers



def extract_product_title(soup, fallback):
    h1 = soup.find("h1")
    if h1:
        title = " ".join(h1.stripped_strings).strip()
        if title:
            return title
    meta = soup.find("meta", attrs={"property": "og:title"})
    if meta and meta.get("content"):
        return meta["content"].strip()
    return fallback


def zelda_product_matches(title):
    value = title.lower()
    return (
        "switch 2" in value
        and "zelda" in value
        and ("40" in value or "aniversario" in value or "anniversary" in value)
        and ("consola" in value or "nintendo switch 2" in value)
    )


def collect_json_availability(node):
    values = []
    if isinstance(node, dict):
        for key, value in node.items():
            if key.lower() == "availability" and isinstance(value, str):
                values.append(value.lower())
            values.extend(collect_json_availability(value))
    elif isinstance(node, list):
        for value in node:
            values.extend(collect_json_availability(value))
    return values


def structured_availability(soup):
    values = []
    for script in soup.find_all("script", attrs={"type": "application/ld+json"}):
        raw = script.string or script.get_text(strip=True)
        if not raw:
            continue
        try:
            data = json.loads(raw)
        except Exception:
            continue
        values.extend(collect_json_availability(data))

    if any(
        marker in value
        for value in values
        for marker in ("outofstock", "soldout", "discontinued")
    ):
        return False, "SIN STOCK"

    if any(
        marker in value
        for value in values
        for marker in ("instock", "preorder", "presale", "limitedavailability")
    ):
        if any("preorder" in value or "presale" in value for value in values):
            return True, "PREVENTA"
        return True, "DISPONIBLE"

    return None


def zelda_availability(text):
    value = text.lower()

    unavailable_terms = (
        "fuera de stock",
        "agotado",
        "producto agotado",
        "no está disponible",
        "no esta disponible",
        "producto no disponible",
        "este producto no está disponible",
        "este producto no esta disponible",
        "temporalmente agotado",
        "precio x confirmar",
        "este producto no tendrá preventa",
        "este producto no tendra preventa",
    )
    if any(term in value for term in unavailable_terms):
        return False, "SIN STOCK"

    if "disponible solo en tienda" in value:
        return True, "DISPONIBLE EN TIENDA"
    if "preventa" in value or "pre-venta" in value:
        return True, "PREVENTA"
    if any(term in value for term in ("agregar al carro", "agregar al carrito", "añadir al carrito", "comprar ahora")):
        return True, "DISPONIBLE"

    return True, "PUBLICACIÓN ACTIVA"


def fetch_zelda_source(source):
    response = requests.get(source["url"], headers=HEADERS, timeout=25)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    text = " ".join(soup.stripped_strings)
    title = extract_product_title(soup, source["title"])

    if not zelda_product_matches(title):
        raise RuntimeError(f"La página ya no parece corresponder a la consola Zelda: {title}")

    structured = structured_availability(soup)
    if structured is not None:
        available, status = structured
    else:
        available, status = zelda_availability(text)
    prices = extract_primary_prices(source, soup, text)
    price = min(prices) if prices else None

    return {
        "available": available,
        "status": status,
        "price": price,
        "url": source["url"],
        "title": title,
    }


def discover_zelda_sources():
    discovered = []
    seen = set()

    for store, search_url in ZELDA_DISCOVERY_PAGES:
        try:
            response = requests.get(search_url, headers=HEADERS, timeout=20)
            response.raise_for_status()
        except Exception as exc:
            print(f"[INFO] Descubrimiento Zelda {store}: {exc}")
            continue

        soup = BeautifulSoup(response.text, "html.parser")
        for anchor in soup.find_all("a", href=True):
            label = " ".join(anchor.stripped_strings).strip()
            if not label or not zelda_product_matches(label):
                continue

            url = urljoin(search_url, anchor["href"])
            key = (store, url)
            if key in seen:
                continue
            seen.add(key)

            discovered.append(
                {
                    "id": f"zelda_discovered_{slugify(store)}_{hashlib.sha1(url.encode('utf-8')).hexdigest()[:12]}",
                    "store": store,
                    "title": label,
                    "url": url,
                }
            )

    return discovered


def build_zelda_alert(source, result):
    price_line = (
        f"💰 <b>{format_clp(result['price'])}</b>\n"
        if result.get("price") is not None
        else "💰 Precio no confirmado\n"
    )
    return (
        "🗡️ <b>SWITCH 2 ZELDA DISPONIBLE</b>\n\n"
        f"🎮 <b>{html.escape(result.get('title') or source['title'])}</b>\n"
        f"🏪 {html.escape(source['store'])}\n"
        f"📌 <b>{html.escape(result['status'])}</b>\n"
        f"{price_line}"
        "⚡ Revisen rápido: esta edición puede agotar stock/preventa.\n\n"
        f"🔗 <a href=\"{html.escape(result['url'], quote=True)}\">Ver publicación</a>"
    )


def process_zelda_sources(state, new_state):
    sources = ZELDA_SOURCES + discover_zelda_sources()

    for source in sources:
        source_id = source["id"]
        try:
            result = fetch_zelda_source(source)
        except Exception as exc:
            print(f"[ERROR] Zelda {source['store']}: {exc}")
            continue

        previous = state.get(source_id, {})
        was_available = bool(previous.get("available"))
        previous_price = previous.get("last_price")
        available = bool(result["available"])
        price = result.get("price")

        print(
            f"[ZELDA] {source['store']}: {result['status']} "
            f"{format_clp(price) if price is not None else 'sin precio'}"
        )

        record = {
            "available": available,
            "last_price": price,
            "last_url": result["url"],
            "last_status": result["status"],
        }

        should_alert = available and (
            not was_available
            or previous_price != price
            or previous.get("last_status") != result["status"]
        )

        if should_alert:
            send_telegram_to(ZELDA_GROUP_ID, build_zelda_alert(source, result))
            print("  -> ALERTA ZELDA ENVIADA AL GRUPO")

        new_state[source_id] = record


def threshold_for(source):
    return BUNDLE_LIMIT if source["kind"] == "bundle" else STANDARD_LIMIT


def build_alert(source, price, url):
    limit = threshold_for(source)
    saving = limit - price

    kind_label = "BUNDLE" if source["kind"] == "bundle" else "CONSOLA"
    return (
        f"🔥 <b>SWITCH 2 EN OFERTA</b>\n\n"
        f"🎮 <b>{html.escape(source['title'])}</b>\n"
        f"🏪 {html.escape(source['store'])}\n"
        f"💰 <b>{format_clp(price)}</b>\n"
        f"✅ {kind_label} bajo tu límite de {format_clp(limit)}\n"
        f"💸 {format_clp(saving)} por debajo de tu máximo\n\n"
        f"🔗 <a href=\"{html.escape(url, quote=True)}\">Ver oferta</a>"
    )


def main():
    if TEST_NOTIFICATION:
        send_telegram(
            "✅ <b>Monitor Switch 2 conectado</b>\n\n"
            "La automatización de GitHub ya puede enviarte alertas por Telegram.\n"
            f"🎮 Consola: {format_clp(STANDARD_LIMIT)} o menos\n"
            f"📦 Bundle: {format_clp(BUNDLE_LIMIT)} o menos\n"
            "🚫 Preventas y Zelda excluidos de tu alerta privada."
        )
        send_telegram_to(
            ZELDA_GROUP_ID,
            "🗡️ <b>Prueba monitor Switch 2 Zelda</b>\n\n"
            "Este grupo recibirá alertas de preventa, reposición o nueva disponibilidad "
            "de la Nintendo Switch 2 The Legend of Zelda 40.º Aniversario.\n"
            "🔗 Las alertas incluirán enlace directo a la publicación."
        )
        print("Notificaciones de prueba enviadas.")
        return

    state = load_state()
    new_state = dict(state)

    def process_offer(source, price, url):
        source_id = source["id"]
        limit = threshold_for(source)
        previous = state.get(source_id, {})
        previous_alerted = previous.get("last_alerted_price")
        previous_alerted_url = previous.get("last_alerted_url")

        print(
            f"[OK] {source['store']} / {source['title']}: "
            f"{format_clp(price)} (límite {format_clp(limit)})"
        )

        record = {
            "last_price": price,
            "last_url": url,
            "last_alerted_price": previous_alerted,
            "last_alerted_url": previous_alerted_url,
        }

        if price <= limit:
            if previous_alerted != price or previous_alerted_url != url:
                send_telegram(build_alert(source, price, url))
                record["last_alerted_price"] = price
                record["last_alerted_url"] = url
                print("  -> ALERTA ENVIADA")
            else:
                print("  -> Misma oferta ya avisada; no se repite.")
        else:
            # Si deja de cumplir el umbral, la próxima vez que vuelva a entrar
            # en oferta se considera un nuevo evento y puede avisarse otra vez.
            record["last_alerted_price"] = None
            record["last_alerted_url"] = None

        new_state[source_id] = record

    # Fuentes directas.
    for source in SOURCES:
        try:
            result = fetch_source(source)
        except Exception as exc:
            print(f"[ERROR] {source['store']} / {source['title']}: {exc}")
            continue

        if result is None:
            continue

        process_offer(source, result["price"], result["url"])

    # Segunda capa: SoloTodo permite descubrir cambios en Paris, Ripley,
    # Lider, Hites y ABC sin depender de una URL fija para cada retailer.
    for product in SOLOTODO_PRODUCTS:
        try:
            offers = fetch_solotodo_offers(product)
        except Exception as exc:
            print(f"[ERROR] SoloTodo / {product['title']}: {exc}")
            continue

        if not offers:
            print(f"[INFO] SoloTodo / {product['title']}: sin ofertas de tiendas objetivo visibles.")
            continue

        for offer in offers:
            process_offer(offer, offer["price"], offer["url"])

    process_zelda_sources(state, new_state)

    save_state(new_state)


if __name__ == "__main__":
    main()
