import sys
import os
import logging
import threading
import socket
import time
import webview
import requests
from flask import Flask
from werkzeug.serving import make_server

# Logging yapılandırması
log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, 'app.log')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def find_free_port(start_port=5001, max_attempts=10):
    """Boş port bul"""
    for port in range(start_port, start_port + max_attempts):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.bind(('127.0.0.1', port))
            sock.close()
            return port
        except OSError:
            continue
    raise RuntimeError(f"Port {start_port}-{start_port+max_attempts} aralığında boş port bulunamadı")


class ServerThread(threading.Thread):
    """Flask server thread yönetimi"""
    def __init__(self, app, port):
        super().__init__(daemon=True)
        self.app = app
        self.port = port
        self.server = None

    def run(self):
        try:
            self.server = make_server('127.0.0.1', self.port, self.app, threaded=True)
            logger.info(f"Flask server başlatıldı: http://127.0.0.1:{self.port}")
            self.server.serve_forever()
        except Exception as e:
            logger.error(f"Server hatası: {e}")

    def shutdown(self):
        if self.server:
            self.server.shutdown()
            logger.info("Flask server kapatıldı")


def create_app():
    """Flask uygulamasını oluştur"""
    try:
        from urun_api import app as flask_app
        logger.info("Backend başarıyla import edildi")
        return flask_app
    except Exception as e:
        logger.error(f"Backend import hatası: {e}")
        app = Flask(__name__)
        from flask_cors import CORS
        CORS(app)

        @app.route('/health')
        def health():
            return {'status': 'ok'}

        return app


def get_static_path():
    """Static dosyaların yolunu bul"""
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))

    return os.path.join(base_path, 'static', 'index.html')


def test_api_connection(port: int) -> dict:
    """
    OpenRouter API bağlantısını test et
    Returns: {"success": bool, "message": str}
    """
    try:
        logger.info("🔍 OpenRouter API test ediliyor...")
        response = requests.get(f"http://127.0.0.1:{port}/test-api", timeout=10)
        data = response.json()

        if data.get("success"):
            logger.info("✅ OpenRouter API bağlantısı başarılı")
        else:
            logger.warning(f"⚠️ API test başarısız: {data.get('message')}")

        return data
    except Exception as e:
        logger.error(f"❌ API test hatası: {e}")
        return {"success": False, "message": f"API test hatası: {str(e)}"}


class Api:
    """PyWebView için API sınıfı"""
    def __init__(self, port):
        self.port = port

    def get_backend_url(self):
        return f"http://127.0.0.1:{self.port}"

    def test_api(self):
        """API test (JS'den çağrılabilir)"""
        return test_api_connection(self.port)


def main():
    """Ana uygulama"""
    try:
        logger.info("=== DM Ürün Çekici Başlatılıyor ===")

        # .env kontrolü
        if not os.path.exists('.env'):
            logger.warning("⚠️ .env dosyası bulunamadı! OPENROUTER_API_KEY eksik olabilir.")

        # Boş port bul
        port = find_free_port()
        logger.info(f"Kullanılacak port: {port}")

        # Flask app oluştur
        flask_app = create_app()

        # Server thread başlat
        server_thread = ServerThread(flask_app, port)
        server_thread.start()

        # Server hazır olana kadar bekle
        logger.info("Backend hazırlanıyor...")
        time.sleep(3)

        # API test
        api_test_result = test_api_connection(port)

        if not api_test_result.get("success"):
            logger.error("❌ API test başarısız! Uygulama yine de açılıyor ama AI özellikleri çalışmayabilir.")

        # Static HTML yolu
        html_path = get_static_path()
        if not os.path.exists(html_path):
            logger.error(f"index.html bulunamadı: {html_path}")
            html_path = f"http://127.0.0.1:{port}"

        # PyWebView penceresi oluştur
        api = Api(port)
        window = webview.create_window(
            title='DM Ürün Veri Çekici - eBay Export Tool',
            url=html_path,
            width=1400,
            height=900,
            resizable=True,
            fullscreen=False,
            min_size=(1000, 700),
            js_api=api
        )

        logger.info("✅ Pencere oluşturuldu, başlatılıyor...")
        webview.start(debug=False)

        # Pencere kapandıktan sonra temizlik
        logger.info("Pencere kapatıldı, temizlik yapılıyor...")
        server_thread.shutdown()

    except Exception as e:
        logger.error(f"❌ Kritik hata: {e}", exc_info=True)
        error_msg = (
            "Uygulama başlatılamadı:\n"
            f"{str(e)}\n\n"
            "Detaylar için logs/app.log dosyasına bakın."
        )

        try:
            import tkinter as tk
            from tkinter import messagebox
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror("Hata", error_msg)
        except Exception:
            print(error_msg)

        sys.exit(1)


if __name__ == '__main__':
    main()
