@echo off
setlocal

echo ========================================
echo DM eBay Exporter - PyInstaller Build
echo ========================================
echo.

echo [1/5] Onceki build dosyalari temizleniyor...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist *.spec del /q *.spec

echo.
echo [2/5] PyInstaller ile paketleme basliyor...
echo.

pyinstaller --onedir ^
  --windowed ^
  --name "DM_eBay_Exporter" ^
  --add-data "static;static" ^
  --hidden-import=selenium ^
  --hidden-import=selenium.webdriver ^
  --hidden-import=selenium.webdriver.chrome.service ^
  --hidden-import=selenium.webdriver.chrome.options ^
  --hidden-import=webdriver_manager ^
  --hidden-import=webdriver_manager.chrome ^
  --hidden-import=bs4 ^
  --hidden-import=flask ^
  --hidden-import=flask_cors ^
  --hidden-import=dotenv ^
  --hidden-import=webview ^
  --hidden-import=openpyxl ^
  --hidden-import=requests ^
  --collect-all selenium ^
  --collect-all webdriver_manager ^
  --collect-all openpyxl ^
  app.py

echo.
echo [3/5] Backend modulleri kopyalaniyor...
copy /Y urun_api.py dist\DM_eBay_Exporter\
copy /Y config.py dist\DM_eBay_Exporter\
copy /Y openrouter_client.py dist\DM_eBay_Exporter\
copy /Y similarity_checker.py dist\DM_eBay_Exporter\
copy /Y ebay_excel_exporter.py dist\DM_eBay_Exporter\

echo.
echo [4/5] .env dosyasi kopyalaniyor...
if exist .env (
  copy /Y .env dist\DM_eBay_Exporter\.env
  echo .env kopyalandi.
) else (
  echo UYARI: .env dosyasi bulunamadi!
)

echo.
echo [5/5] Excel template kopyalaniyor...
if exist eBay-category-listing-template-Jan-11-2026-15-0-23.xlsx (
  copy /Y eBay-category-listing-template-Jan-11-2026-15-0-23.xlsx dist\DM_eBay_Exporter\
  echo Template kopyalandi.
) else (
  echo UYARI: Excel template bulunamadi!
)

if not exist dist\DM_eBay_Exporter\logs mkdir dist\DM_eBay_Exporter\logs

echo.
echo ========================================
echo BUILD TAMAMLANDI!
echo ========================================
echo.
echo Calistirilabilir dosya:
echo dist\DM_eBay_Exporter\DM_eBay_Exporter.exe
echo.
pause
