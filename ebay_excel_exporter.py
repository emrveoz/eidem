import os
import re
from datetime import datetime
from openpyxl import Workbook

def _safe_price(price_str):
    if price_str is None:
        return ""
    s = str(price_str).strip()
    if not s:
        return ""
    clean = re.sub(r"[^\d,\.]", "", s).replace(",", ".")
    return clean

def _join_images(images):
    if not images:
        return ""
    return "|".join(images[:12])

def _resolve(header, product):
    # başarısızsa sadece Title alanına hata yaz
    if not product.get("success"):
        if header == "Title":
            return f"HATA: {product.get('error') or product.get('message') or 'Bilinmeyen hata'}"
        return ""

    specs = (product.get("specifications") or {})
    manufacturer = (product.get("manufacturer") or {})
    images = product.get("resimler") or []

    mapping = {
        "*Action(SiteID=Germany|Country=DE|Currency=EUR|Version=1193)": "Add",
        "Custom label (SKU)": product.get("ean", ""),
        "Title": (product.get("ebay_title") or product.get("dm_baslik") or "")[:80],
        "P:EAN": product.get("ean", ""),
        "Start price": _safe_price(product.get("fiyat") or product.get("price")),
        "Quantity": "1",
        "Item photo URL": _join_images(images),
        "Description": product.get("html_description", ""),

        "C:Marke": specs.get("marke", ""),
        "C:Formulierung": specs.get("formulierung", ""),
        "C:Wirksame Inhaltsstoffe": specs.get("wirksame_inhaltsstoffe", ""),
        "C:Produktart": specs.get("produktart", ""),
        "C:Herstellernummer": specs.get("herstellernummer", ""),
        "C:Anzahl der Tabletten": specs.get("anzahl_tabletten", ""),
        "C:Hauptverwendungszweck": specs.get("hauptverwendungszweck", ""),
        "C:Inhaltsstoffe": specs.get("inhaltsstoffe", ""),
        "C:Versorgung": specs.get("versorgung", ""),

        "Manufacturer Name": manufacturer.get("name", ""),
        "Manufacturer AddressLine1": manufacturer.get("address_line1", ""),
        "Manufacturer City": manufacturer.get("city", ""),
        "Manufacturer Country": manufacturer.get("country", ""),
        "Manufacturer PostalCode": manufacturer.get("postal_code", ""),
    }

    return mapping.get(header, "")

def export_products_xlsx(products, headers, out_dir="exports"):
    wb = Workbook()
    ws = wb.active
    ws.title = "Export"

    # header
    ws.append(headers)

    # rows
    for p in products:
        row = [_resolve(h, p) for h in headers]
        ws.append(row)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"ebay_export_{ts}.xlsx"
    filepath = os.path.join(out_dir, filename)
    wb.save(filepath)
    return filepath, filename
