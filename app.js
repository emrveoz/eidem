// Global state
let backendPort = 5001;
let allProducts = [];

// DOM Elements
const urlList = document.getElementById('urlList');
const urlCount = document.getElementById('urlCount');
const clearUrlsBtn = document.getElementById('clearUrlsBtn');
const fetchAllBtn = document.getElementById('fetchAllBtn');
const progressSection = document.getElementById('progressSection');
const productsSection = document.getElementById('productsSection');
const urlInput = document.getElementById('urlInput');
const addUrlBtn = document.getElementById('addUrlBtn');
const productsTableHeader = document.getElementById('productsTableHeader');
const productsTableBody = document.getElementById('productsTableBody');
const exportBtn = document.getElementById('exportBtn');
const apiStatus = document.getElementById('apiStatus');

const toggleTableBtn = document.getElementById('toggleTableBtn');
const productsTableWrapper = document.getElementById('productsTableWrapper');

let exportHeaders = [];

// Backend URL
let backendUrl = `http://127.0.0.1:${backendPort}`;

document.addEventListener('DOMContentLoaded', () => {
  if (window.pywebview && window.pywebview.api) {
    window.pywebview.api.get_backend_url().then(url => {
      backendUrl = url;
      backendPort = url.split(':').pop();
      testApiConnection();
    });
  } else {
    testApiConnection();
  }

  urlList.addEventListener('input', updateUrlCount);
  addUrlBtn.addEventListener('click', addUrlFromInput);
  urlInput.addEventListener('keydown', handleUrlInputKeydown);
  clearUrlsBtn.addEventListener('click', clearUrls);
  fetchAllBtn.addEventListener('click', fetchAllProducts);
  exportBtn.addEventListener('click', exportToExcel);

  toggleTableBtn.addEventListener('click', toggleTableFullscreen);

  loadExportHeaders();
  updateUrlCount();
});

// API Test
async function testApiConnection() {
  try {
    const response = await fetch(`${backendUrl}/health`);
    const data = await response.json();

    const statusDot = apiStatus.querySelector('.status-dot');
    const statusText = apiStatus.querySelector('.status-text');

    if (data.status === 'ok') {
      statusDot.className = 'status-dot success';
      statusText.textContent = '✅ Backend çalışıyor';
      apiStatus.className = 'api-status success';
    } else {
      statusDot.className = 'status-dot error';
      statusText.textContent = '❌ Backend hatası';
      apiStatus.className = 'api-status error';
    }
  } catch (error) {
    const statusDot = apiStatus.querySelector('.status-dot');
    const statusText = apiStatus.querySelector('.status-text');
    statusDot.className = 'status-dot error';
    statusText.textContent = '❌ Backend erişilemiyor';
    apiStatus.className = 'api-status error';
  }
}

// URL Counter
function updateUrlCount() {
  const urls = getUrls();
  urlCount.textContent = `${urls.length} URL`;
  fetchAllBtn.disabled = urls.length === 0;
}

function getUrls() {
  return urlList.value
    .split('\n')
    .map(u => u.trim())
    .filter(u => u.length > 0 && u.includes('dm.de'));
}

function clearUrls() {
  urlList.value = '';
  urlInput.value = '';
  updateUrlCount();
}

function handleUrlInputKeydown(event) {
  if (event.key === 'Enter') {
    event.preventDefault();
    addUrlFromInput();
  }
}

function addUrlFromInput() {
  const value = urlInput.value.trim();
  if (!value) return;

  if (!value.includes('dm.de')) {
    showToast('❌ Lütfen dm.de linki girin', 'error');
    return;
  }

  const current = urlList.value.trim();
  urlList.value = current ? `${current}\n${value}` : value;
  urlInput.value = '';
  urlInput.focus();
  updateUrlCount();
}

// Headers
async function loadExportHeaders() {
  try {
    const response = await fetch(`${backendUrl}/export-headers`);
    const data = await response.json();
    if (data.success && Array.isArray(data.headers)) {
      exportHeaders = data.headers;
      renderTableHeader();
    } else {
      showToast('❌ Export başlıkları alınamadı', 'error');
    }
  } catch (error) {
    console.error('Header yükleme hatası:', error);
    showToast('❌ Export başlıkları alınamadı', 'error');
  }
}

function renderTableHeader() {
  productsTableHeader.innerHTML = '';
  exportHeaders.forEach(header => {
    const th = document.createElement('th');
    th.textContent = header;
    productsTableHeader.appendChild(th);
  });
}

// Fetch all
async function fetchAllProducts() {
  const urls = getUrls();

  if (urls.length === 0) {
    showToast('❌ Lütfen en az bir URL girin', 'error');
    return;
  }

  allProducts = [];
  productsTableBody.innerHTML = '';

  fetchAllBtn.disabled = true;
  urlList.disabled = true;
  urlInput.disabled = true;
  addUrlBtn.disabled = true;

  showProgress(true);
  updateProgress(0, urls.length, 'Başlatılıyor...');

  for (let i = 0; i < urls.length; i++) {
    const url = urls[i];
    updateProgress(i, urls.length, `İşleniyor: ${i + 1}/${urls.length}`);

    try {
      const response = await fetch(`${backendUrl}/urun?url=${encodeURIComponent(url)}`);
      const data = await response.json();

      allProducts.push(data);
      addProductRow(data);
    } catch (error) {
      console.error(`URL hatası [${i + 1}]:`, error);
      const fail = { success: false, url, error: error.message };
      allProducts.push(fail);
      addProductRow(fail);
    }
  }

  updateProgress(urls.length, urls.length, '✅ Tamamlandı!');
  setTimeout(() => showProgress(false), 800);

  fetchAllBtn.disabled = false;
  urlList.disabled = false;
  urlInput.disabled = false;
  addUrlBtn.disabled = false;

  showProductsSection();
  updateSummary();

  const successfulCount = allProducts.filter(p => p.success).length;
  exportBtn.disabled = successfulCount === 0;
}

function showProgress(show) {
  progressSection.classList.toggle('hidden', !show);
}

function updateProgress(current, total, message) {
  const percent = total > 0 ? (current / total) * 100 : 0;
  document.getElementById('progressFill').style.width = `${percent}%`;
  document.getElementById('progressCount').textContent = `${current}/${total}`;
  document.getElementById('progressMessage').textContent = message;
}

// Table
function addProductRow(product) {
  if (!exportHeaders.length) return;

  const row = document.createElement('tr');
  if (!product.success) row.classList.add('row-error');

  exportHeaders.forEach(header => {
    const cell = document.createElement('td');
    cell.textContent = resolveHeaderValue(header, product);
    row.appendChild(cell);
  });

  productsTableBody.appendChild(row);
}

function resolveHeaderValue(header, product) {
  if (!product.success) {
    return header === 'Title'
      ? `HATA: ${product.error || product.message || 'Bilinmeyen hata'}`
      : '';
  }

  const map = {
    '*Action(SiteID=Germany|Country=DE|Currency=EUR|Version=1193)': 'Add',
    'Custom label (SKU)': product.ean || '',
    'Title': (product.ebay_title || product.dm_baslik || '').slice(0, 80),
    'P:EAN': product.ean || '',
    'Start price': product.fiyat || product.price || '',
    'Quantity': '1',
    'Item photo URL': (product.resimler || []).join('|'),

    'Description': product.html_description || '',

    // Custom fields (boş olabilir)
    'C:Marke': product.specifications?.marke || product.marke || '',
    'C:Formulierung': product.specifications?.formulierung || product.formulierung || '',
    'C:Produktart': product.specifications?.produktart || product.produktart || '',
    'C:Wirksame Inhaltsstoffe': product.specifications?.wirksame_inhaltsstoffe || '',
    'C:Herstellernummer': product.specifications?.herstellernummer || '',
    'C:Anzahl der Tabletten': product.specifications?.anzahl_tabletten || '',
    'C:Hauptverwendungszweck': product.specifications?.hauptverwendungszweck || '',
    'C:Inhaltsstoffe': product.specifications?.inhaltsstoffe || '',
    'C:Versorgung': product.specifications?.versorgung || '',

    'Manufacturer Name': product.manufacturer?.name || '',
    'Manufacturer AddressLine1': product.manufacturer?.address_line1 || '',
    'Manufacturer City': product.manufacturer?.city || '',
    'Manufacturer Country': product.manufacturer?.country || '',
    'Manufacturer PostalCode': product.manufacturer?.postal_code || '',
  };

  return map[header] ?? '';
}

function showProductsSection() {
  productsSection.classList.remove('hidden');
  productsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function updateSummary() {
  const successful = allProducts.filter(p => p.success).length;
  const failed = allProducts.length - successful;

  document.getElementById('successCount').textContent = successful;
  document.getElementById('errorCount').textContent = failed;
}

// Fullscreen toggle
function toggleTableFullscreen() {
  document.body.classList.toggle('table-fullscreen');
  const isFs = document.body.classList.contains('table-fullscreen');
  toggleTableBtn.textContent = isFs ? '⤢ Tam ekrandan çık' : '⛶ Tam ekran tablo';
}

// Export -> downloads XLSX
async function exportToExcel() {
  const successfulProducts = allProducts.filter(p => p.success);
  if (successfulProducts.length === 0) {
    showToast('❌ Export edilecek başarılı ürün yok', 'error');
    return;
  }

  exportBtn.disabled = true;
  exportBtn.innerHTML = '<span class="spinner"></span> Export hazırlanıyor...';

  try {
    const response = await fetch(`${backendUrl}/export-excel`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ products: successfulProducts })
    });

    if (!response.ok) {
      const errText = await response.text();
      console.error(errText);
      showToast('❌ Export hatası (server)', 'error');
      return;
    }

    const blob = await response.blob();
    const cd = response.headers.get('content-disposition') || '';
    let filename = 'ebay_export.xlsx';
    const m = /filename="?([^"]+)"?/i.exec(cd);
    if (m && m[1]) filename = m[1];

    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    a.remove();
    window.URL.revokeObjectURL(url);

    showToast(`✅ Export indirildi: ${filename}`, 'success');
  } catch (error) {
    console.error('Export hatası:', error);
    showToast('❌ Export sırasında hata oluştu', 'error');
  } finally {
    exportBtn.disabled = false;
    exportBtn.innerHTML = '<span class="btn-icon">📥</span><span class="btn-text">Excel İndir (eBay Vorlage)</span>';
  }
}

// Toast
function showToast(message, type = 'info') {
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.textContent = message;

  document.body.appendChild(toast);

  setTimeout(() => toast.classList.add('show'), 50);

  setTimeout(() => {
    toast.classList.remove('show');
    setTimeout(() => toast.remove(), 250);
  }, 3000);
}

// Modal functions kept (optional)
function closeProductModal() {
  document.getElementById('productModal').classList.add('hidden');
}
window.closeProductModal = closeProductModal;
