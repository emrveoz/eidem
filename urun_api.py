from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import re
import os
import sys
import logging
import traceback

# Proje klasörünü path'e ekle
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config
from ebay_excel_exporter import export_products_xlsx

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/app.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})


def parse_manufacturer_info(text):
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    result = {
        "name": lines[0] if len(lines) > 0 else "",
        "address_line1": lines[1] if len(lines) > 1 else "",
        "city": "",
        "postal_code": "",
        "country": "Deutschland"
    }
    for line in lines:
        m = re.search(r"(\d{4,5})\s+(.+)", line)
        if m:
            result["postal_code"] = m.group(1)
            result["city"] = m.group(2)
        if "deutschland" in line.lower():
            result["country"] = "Deutschland"
    return result


def get_all_images(soup):
    urls = []
    for i in range(1, 11):
        sel = f"li:nth-of-type({i}) .p-xxxs img"
        tag = soup.select_one(sel)
        if not tag:
            continue
        src = tag.get("src") or tag.get("data-src") or ""
        if not src and tag.get("srcset"):
            src = tag.get("srcset").split(",")[0].strip().split(" ")[0]
        if not src:
            continue
        if src.startswith("/"):
            src = "https://www.dm.de" + src
        src = re.sub(r"h_\d+,w_\d+", "h_1200,w_1200", src)
        if src not in urls:
            urls.append(src)
    return urls


def temizle_aciklama(text):
    text = re.sub(r"dm-Artikelnummer:.*?(\n|$)", "", text, flags=re.IGNORECASE)
    text = re.sub(r"Dosierungsempfehlung:.*?(\n|$)", "", text, flags=re.IGNORECASE)
    text = re.sub(r"Hinweis:.*?(Hergestellt|$)", "", text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"Hergestellt.*?(\n|$)", "", text, flags=re.IGNORECASE)
    return text.strip()


def veri_cek(url):
    logger.info(f"🔄 Veri çekiliyor: {url}")

    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = None
    try:
        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=options
        )

        driver.get(url)
        WebDriverWait(driver, 12).until(EC.presence_of_element_located((By.TAG_NAME, "h1")))
        soup = BeautifulSoup(driver.page_source, "html.parser")

        baslik_el = soup.select_one("h1")
        baslik = baslik_el.get_text(strip=True) if baslik_el else "Başlık bulunamadı"

        fiyat_el = soup.select_one(".text-xxl span.text-color2")
        fiyat = fiyat_el.get_text(strip=True) if fiyat_el else ""

        aciklama_nodes = soup.select(".gap-m div:nth-of-type(2) .whitespace-pre-line div")
        dm_aciklama = temizle_aciklama("\n".join(n.get_text(" ", strip=True) for n in aciklama_nodes))

        ean_el = soup.select_one(".pdd_1qsttl15 div:nth-of-type(2)")
        ean = re.sub(r"[^0-9]", "", ean_el.get_text()) if ean_el else ""

        addr = soup.select_one("[data-dmid='Anschrift des Unternehmens-content'] .whitespace-pre-line div")
        manufacturer = parse_manufacturer_info(addr.get_text("\n", strip=True) if addr else "")

        resimler = get_all_images(soup)

        # AI şu an opsiyonel: yoksa da doldur.
        ebay_title = baslik[:80]
        bullet_points = []
        html_description = f"<p>{dm_aciklama}</p>" if dm_aciklama else f"<p>{baslik}</p>"

        specs = {
            "marke": "",
            "produktart": "",
            "formulierung": "",
            "wirksame_inhaltsstoffe": "",
            "herstellernummer": "",
            "anzahl_tabletten": "",
            "hauptverwendungszweck": "",
            "inhaltsstoffe": "",
            "versorgung": "",
        }

        result = {
            "success": True,
            "url": url,
            "dm_baslik": baslik,
            "dm_aciklama": dm_aciklama,
            "fiyat": fiyat,
            "ean": ean,
            "resimler": resimler,
            "manufacturer": manufacturer,

            "ebay_title": ebay_title,
            "bullet_points": bullet_points,
            "html_description": html_description,
            "specifications": specs
        }

        logger.info(f"✅ Ürün başarıyla işlendi: {baslik}")
        return result

    except Exception as e:
        logger.error(f"❌ Hata: {e}")
        logger.error(traceback.format_exc())
        return {
            "success": False,
            "url": url,
            "error": str(e),
            "message": f"Veri çekme hatası: {str(e)}"
        }
    finally:
        if driver:
            driver.quit()


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "message": "Backend çalışıyor"})


@app.route("/urun", methods=["GET"])
def urun_endpoint():
    url = request.args.get("url")
    if not url:
        return jsonify({"success": False, "error": "URL gerekli"}), 400

    try:
        result = veri_cek(url)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Endpoint hatası: {e}")
        return jsonify({
            "success": False,
            "url": url,
            "error": str(e),
            "message": "Sunucu hatası"
        }), 500


@app.route("/export-headers", methods=["GET"])
def export_headers():
    return jsonify({"success": True, "headers": config.EXPORT_HEADERS})


@app.route("/export-excel", methods=["POST"])
def export_excel():
    try:
        data = request.get_json() or {}
        products = data.get("products", [])
        if not products:
            return jsonify({"success": False, "message": "Ürün listesi boş"}), 400

        os.makedirs("exports", exist_ok=True)
        filepath, filename = export_products_xlsx(products, config.EXPORT_HEADERS, out_dir="exports")

        # dosyayı indir
        return send_file(
            filepath,
            as_attachment=True,
            download_name=filename,
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    except Exception as e:
        logger.error(f"Export hatası: {e}")
        logger.error(traceback.format_exc())
        return jsonify({"success": False, "message": str(e)}), 500


if __name__ == "__main__":
    os.makedirs('logs', exist_ok=True)
    app.run(host='127.0.0.1', port=5001, debug=True)
