diff --git a/README_RUN.txt b/README_RUN.txt
new file mode 100644
index 0000000000000000000000000000000000000000..10516519a22ed5994cd0fdb5be59567e0e70bbdf
--- /dev/null
+++ b/README_RUN.txt
@@ -0,0 +1,38 @@
+DM Ürün Veri Çekici - Çalıştırma ve EXE Oluşturma
+
+1) Gereksinimler
+- Windows 10/11
+- Python 3.10+ (kurulumda “Add Python to PATH” işaretli olsun)
+- Google Chrome kurulu olmalı
+
+2) Kurulum
+Komut İstemi (cmd) ile proje klasörüne girin:
+  cd C:\Users\Emrah\Desktop\dm_proje
+
+Sanal ortam oluşturun ve aktif edin:
+  python -m venv venv
+  venv\Scripts\activate
+
+Gerekli paketleri kurun:
+  pip install -r requirements.txt
+
+3) Uygulamayı Çalıştırma (EXE olmadan)
+  python app.py
+
+3.1) "diff --git ..." Hatası (SyntaxError: invalid syntax)
+- Eğer app.py veya urun_api.py dosyasının içinde en üstte "diff --git ..." gibi bir satır
+  görüyorsanız, dosya yanlışlıkla patch metni ile kaydedilmiştir.
+- Çözüm: bana dosyaları tekrar isteyin ya da repo içindeki doğru dosyaları indirip
+  Windows’a kopyalayın. Doğru dosyada ilk satır "import ..." ile başlamalıdır.
+
+4) EXE Oluşturma (PyInstaller)
+- build.bat dosyasını çift tıklayın veya cmd’den çalıştırın:
+  build.bat
+
+- Çıktı klasörü:
+  dist\DM_eBay_Exporter\DM_eBay_Exporter.exe
+
+5) Önemli Notlar
+- OpenRouter API anahtarı şu an gerekli değildir. AI üretimi kapalı çalışır.
+- Eğer ileride AI kullanmak isterseniz .env dosyasına OPENROUTER_API_KEY ekleyin.
+- EXE çalışırken Chrome bulunamazsa Selenium hata verebilir.
