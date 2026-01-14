"""
OpenRouter API İstemcisi
ALMANCA metin üretimi için
"""
import logging
from typing import Optional, Dict, List

import requests
import config

logger = logging.getLogger(__name__)


class OpenRouterClient:
    """OpenRouter API istemcisi"""

    def __init__(self):
        self.api_key = config.OPENROUTER_API_KEY
        self.url = config.OPENROUTER_URL
        self.model = config.OPENROUTER_MODEL
        self.timeout = config.OPENROUTER_TIMEOUT
        self.last_error: Optional[str] = None

        if not self.api_key:
            logger.error("OPENROUTER_API_KEY bulunamadı!")

    def test_connection(self) -> Dict:
        """API bağlantısını test et"""
        response = self._call_api(prompt="Antworte nur mit 'OK'.", max_tokens=10)

        if response is None:
            return {"success": False, "message": self.last_error or "API yanıtı alınamadı"}

        if "ok" in response.lower():
            return {"success": True, "message": "API bağlantısı başarılı"}

        preview = response.strip().replace("\n", " ")
        return {"success": True, "message": f"API yanıtı alındı (beklenen 'OK' değil): {preview[:80]}"}

    def _call_api(self, prompt: str, max_tokens: int = None, temperature: float = None) -> Optional[str]:
        self.last_error = None

        if not self.api_key:
            self.last_error = "API key eksik"
            logger.error(self.last_error)
            return None

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://localhost",
        }

        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature if temperature is not None else config.AI_TEMPERATURE,
            "max_tokens": max_tokens if max_tokens is not None else config.AI_MAX_TOKENS,
        }

        try:
            resp = requests.post(self.url, headers=headers, json=payload, timeout=self.timeout)

            if resp.status_code != 200:
                self.last_error = f"HTTP {resp.status_code}: {resp.text[:300]}"
                logger.error(self.last_error)
                return None

            data = resp.json()

            if "error" in data:
                self.last_error = f"API error: {data['error']}"
                logger.error(self.last_error)
                return None

            if "choices" not in data or not data["choices"]:
                self.last_error = f"API format hatası: {str(data)[:300]}"
                logger.error(self.last_error)
                return None

            content = data["choices"][0]["message"]["content"].strip()
            if not content:
                self.last_error = "API boş içerik döndürdü"
                logger.error(self.last_error)
                return None

            return content

        except requests.Timeout:
            self.last_error = "API timeout"
            logger.error(self.last_error)
            return None
        except Exception as e:
            self.last_error = f"API exception: {e}"
            logger.error(self.last_error)
            return None

    def generate_ebay_title(self, product_name: str, brand: str = "", specs: str = "") -> str:
        """eBay başlık üret (ALMANCA, max 80 karakter)"""
        prompt = f"""
Erstelle einen eBay-Titel auf Deutsch für dieses Produkt.

Produktname: {product_name}
Marke: {brand or "unbekannt"}
Spezifikationen: {specs or "keine"}

REGELN:
- Maximal 80 Zeichen
- Auf Deutsch
- Keine Anführungszeichen
- Format: Marke + Produkt + Menge/Volumen (wenn sinnvoll)
- Klar und prägnant
- Keine Werbewörter wie "NEU", "ORIGINAL"

Antworte NUR mit dem Titel, nichts anderes.
""".strip()

        result = self._call_api(prompt, max_tokens=80, temperature=0.6)
        if result:
            result = result.strip().strip('"').strip("'")
            if len(result) > 80:
                result = result[:80]
            return result

        fallback = f"{brand} {product_name}".strip()
        return fallback[:80]

    def generate_bullet_points(self, product_name: str, description: str, specs: Dict) -> List[str]:
        """Bullet points üret (ALMANCA, 4-6 adet)"""
        specs_text = "\n".join([f"{k}: {v}" for k, v in specs.items() if v]) or "keine"

        prompt = f"""
Erstelle 4-6 Bullet Points auf Deutsch für eBay.

Produktname: {product_name}
Beschreibung (Auszug): {description[:500]}
Spezifikationen:
{specs_text}

REGELN:
- Auf Deutsch
- Direkt Bullet Points, keine Einleitung
- Keine Wiederholungen
- Keine Floskeln wie "Beschreibung", "SEO"
- Jeder Punkt kurz & nutzerorientiert

Format:
- Punkt 1
- Punkt 2
- Punkt 3
- Punkt 4
""".strip()

        result = self._call_api(prompt, max_tokens=300, temperature=0.7)

        bullets: List[str] = []
        if result:
            for line in result.splitlines():
                line = line.strip()
                if line.startswith(("-", "•", "*")):
                    b = line[1:].strip()
                    if b:
                        bullets.append(b[:160])

        while len(bullets) < 4:
            bullets.append(f"Hochwertige Qualität für {product_name}"[:160])

        return bullets[:6]

    def generate_html_description(self, product_name: str, description: str, bullets: List[str], specs: Dict) -> str:
        """HTML açıklama üret (ALMANCA, eBay uyumlu)"""
        specs_text = "\n".join([f"{k}: {v}" for k, v in specs.items() if v])
        bullets_text = "\n".join([f"- {b}" for b in bullets])

        prompt = f"""
Erstelle eine eBay-kompatible HTML-Produktbeschreibung auf Deutsch.

Produktname: {product_name}
Originalbeschreibung (Auszug): {description[:800]}
Vorteile:
{bullets_text}
Spezifikationen:
{specs_text or "keine"}

REGELN:
- NUR HTML (kein Markdown, keine Erklärungen)
- Keine <script> oder <style>
- Struktur: zuerst <ul><li>..</li></ul>, danach 1-2 <p>
- Keine Wörter wie "Beschreibung", "SEO", "DM", "dm.de"

Antworte NUR mit HTML.
""".strip()

        result = self._call_api(prompt, max_tokens=700, temperature=0.7)
        if result and "<" in result:
            return result.strip()

        lis = "".join([f"<li>{b}</li>" for b in bullets[:6]])
        return f"<ul>{lis}</ul><p>{product_name}</p>"
