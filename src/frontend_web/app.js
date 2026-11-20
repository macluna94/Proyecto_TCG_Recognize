const API_BASE = window.location.origin.startsWith("http") ? "" : "http://127.0.0.1:8000";

let selectedFile = null;
let lastOcrRaw = null;
let albumData = [];
let albumFilter = "all";
let historyData = [];
let historyFilter = "all";

const VIEW_TITLES = {
  escaner: "Escáner",
  album: "Álbum",
  dashboard: "Dashboard",
  historial: "Historial",
};

// ---------- Navegación ----------
function switchView(view) {
  document.querySelectorAll(".view-section").forEach((el) => el.classList.add("hidden"));
  document.getElementById(`view-${view}`).classList.remove("hidden");
  document.getElementById("mobile-header-title").textContent = VIEW_TITLES[view] || view;

  document.querySelectorAll(".nav-btn-desktop").forEach((btn) => {
    const active = btn.dataset.view === view;
    btn.className = active
      ? "nav-btn-desktop flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-sm font-semibold bg-[#FEE2E2] text-[#EF4444] shadow-xs transition-all"
      : "nav-btn-desktop flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-sm font-medium text-gray-600 hover:bg-gray-100 hover:text-gray-900 transition-all";
  });

  document.querySelectorAll(".nav-btn-mobile").forEach((btn) => {
    const active = btn.dataset.view === view;
    const wrap = btn.querySelector(".icon-wrap");
    btn.classList.toggle("text-[#EF4444]", active);
    btn.classList.toggle("font-semibold", active);
    btn.classList.toggle("text-gray-500", !active);
    wrap.className = active
      ? "icon-wrap w-10 h-8 rounded-xl flex items-center justify-center bg-[#FEE2E2] text-[#EF4444] transition-all"
      : "icon-wrap w-10 h-8 rounded-xl flex items-center justify-center transition-all";
  });

  if (view === "album") loadCollection();
  if (view === "dashboard") loadStats();
  if (view === "historial") loadHistory();
}

// ---------- Escáner ----------
const dropzone = document.getElementById("dropzone");
const fileInput = document.getElementById("file-input");
const cameraInput = document.getElementById("camera-input");

dropzone.addEventListener("click", () => fileInput.click());
dropzone.addEventListener("dragover", (e) => {
  e.preventDefault();
  dropzone.classList.add("border-[#EF4444]");
});
dropzone.addEventListener("dragleave", () => dropzone.classList.remove("border-[#EF4444]"));
dropzone.addEventListener("drop", (e) => {
  e.preventDefault();
  dropzone.classList.remove("border-[#EF4444]");
  if (e.dataTransfer.files[0]) handleFileSelect(e.dataTransfer.files[0]);
});

fileInput.addEventListener("change", (e) => {
  if (e.target.files[0]) handleFileSelect(e.target.files[0]);
});
cameraInput.addEventListener("change", (e) => {
  if (e.target.files[0]) handleFileSelect(e.target.files[0]);
});

function handleFileSelect(file) {
  selectedFile = file;
  const preview = document.getElementById("preview-image");
  preview.src = URL.createObjectURL(file);
  preview.classList.remove("hidden");
  document.getElementById("dropzone-placeholder").classList.add("hidden");
  document.getElementById("btn-scan").disabled = false;
}

function resetScanner() {
  selectedFile = null;
  fileInput.value = "";
  cameraInput.value = "";
  document.getElementById("preview-image").classList.add("hidden");
  document.getElementById("dropzone-placeholder").classList.remove("hidden");
  document.getElementById("btn-scan").disabled = true;
  document.getElementById("result-content").classList.add("hidden");
  document.getElementById("result-empty").classList.remove("hidden");
}

async function runScan() {
  if (!selectedFile) return;
  const loader = document.getElementById("scan-loader");
  const btn = document.getElementById("btn-scan");
  loader.classList.remove("hidden");
  btn.disabled = true;

  try {
    const formData = new FormData();
    formData.append("file", selectedFile);

    const res = await fetch(`${API_BASE}/api/v1/scan`, { method: "POST", body: formData });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();

    lastOcrRaw = data.ocr_raw;
    document.getElementById("ocr-json-output").textContent = JSON.stringify(data.ocr_raw, null, 2);

    document.getElementById("result-empty").classList.add("hidden");
    document.getElementById("result-content").classList.remove("hidden");

    const match = data.match || {};
    const card = match.card;

    if (data.success && card) {
      document.getElementById("res-status-dot").className = "w-2.5 h-2.5 rounded-full bg-emerald-500";
      document.getElementById("res-status-title").textContent = "Identificada con éxito";
      document.getElementById("res-score-badge").textContent = `${match.score}% MATCH`;
      document.getElementById("res-score-badge").className =
        "inline-flex items-center px-2.5 py-1 rounded-full font-mono text-xs font-bold bg-[#D1FAE5] text-[#065F46] border border-emerald-200";
      document.getElementById("res-card-img").src = card.image_url || "";
      document.getElementById("res-name").textContent = card.name;
      document.getElementById("res-number").textContent = `#${card.number}`;
      document.getElementById("res-rarity").textContent = `★ ${card.rarity || "Special"}`;
      const isExact = match.match_type === "exact_number";
      document.getElementById("res-method-badge").textContent = match.match_type;
      document.getElementById("res-method-badge").className = isExact
        ? "px-2.5 py-0.5 rounded-full font-mono text-[11px] font-bold bg-[#D1FAE5] text-[#065F46]"
        : "px-2.5 py-0.5 rounded-full font-mono text-[11px] font-bold bg-[#E0F2FE] text-[#0369A1]";
    } else {
      document.getElementById("res-status-dot").className = "w-2.5 h-2.5 rounded-full bg-red-500";
      document.getElementById("res-status-title").textContent = "No se encontró coincidencia";
      document.getElementById("res-score-badge").textContent = "0% MATCH";
      document.getElementById("res-score-badge").className =
        "inline-flex items-center px-2.5 py-1 rounded-full font-mono text-xs font-bold bg-[#FEE2E2] text-[#991B1B] border border-red-200";
      document.getElementById("res-card-img").src = document.getElementById("preview-image").src;
      document.getElementById("res-name").textContent = "Carta no identificada";
      document.getElementById("res-number").textContent = "--";
      document.getElementById("res-rarity").textContent = "Revisa los datos crudos del OCR";
      document.getElementById("res-method-badge").textContent = "none";
      document.getElementById("res-method-badge").className =
        "px-2.5 py-0.5 rounded-full font-mono text-[11px] font-bold bg-[#FEE2E2] text-[#991B1B]";
    }
  } catch (err) {
    alert("Error conectando con FastAPI. Verifica que uvicorn esté corriendo en el puerto 8000.");
    console.error(err);
  } finally {
    loader.classList.add("hidden");
    btn.disabled = false;
  }
}

function toggleRawOcr() {
  const content = document.getElementById("ocr-content");
  const chevron = document.getElementById("ocr-chevron");
  const isHidden = content.classList.toggle("hidden");
  content.classList.toggle("flex", !isHidden);
  chevron.style.transform = isHidden ? "rotate(0deg)" : "rotate(180deg)";
}

function copyOcrJson(btn) {
  if (!lastOcrRaw) return;
  navigator.clipboard?.writeText(JSON.stringify(lastOcrRaw, null, 2));
  const span = btn.querySelector("span:last-child");
  span.textContent = "¡Copiado!";
  setTimeout(() => (span.textContent = "Copiar JSON"), 1500);
}

// ---------- Álbum ----------
async function loadCollection() {
  try {
    const res = await fetch(`${API_BASE}/api/v1/collection`);
    const data = await res.json();
    albumData = data.cards || [];

    document.getElementById("album-physical-count").textContent = data.total_physical;
    document.getElementById("album-unique-count").textContent = `${data.unique_owned} / ${data.total_cards}`;
    document.getElementById("album-progress-label").textContent = `${data.progress_pct}% Completado`;
    document.getElementById("album-missing-label").textContent = `${data.total_cards - data.unique_owned} faltantes`;
    document.getElementById("album-progress-bar").style.width = `${data.progress_pct}%`;
    renderAlbumGrid();
  } catch (err) {
    console.error("Error cargando álbum:", err);
  }
}

function setAlbumFilter(filter, btn) {
  albumFilter = filter;
  document.querySelectorAll(".album-filter-btn").forEach((b) => {
    b.className =
      "album-filter-btn px-3.5 py-1.5 rounded-full bg-gray-50 border border-gray-200 text-gray-600 hover:bg-gray-100 font-mono text-xs font-semibold";
  });
  btn.className = "album-filter-btn px-3.5 py-1.5 rounded-full bg-[#EF4444] text-white font-mono text-xs font-bold";
  renderAlbumGrid();
}

function renderAlbumGrid() {
  const q = (document.getElementById("album-search").value || "").toLowerCase().trim();
  const grid = document.getElementById("album-grid");

  const filtered = albumData.filter((c) => {
    if (albumFilter === "owned" && !c.owned) return false;
    if (albumFilter === "missing" && c.owned) return false;
    if (q && !c.name.toLowerCase().includes(q) && !c.number.toLowerCase().includes(q)) return false;
    return true;
  });

  if (!filtered.length) {
    grid.innerHTML = `<div class="col-span-full text-center py-12 text-sm text-gray-400">No hay cartas que coincidan con el filtro.</div>`;
    return;
  }

  grid.innerHTML = filtered
    .map((c) => {
      if (c.owned) {
        return `
          <div onclick='openCardModal(${JSON.stringify(c).replace(/'/g, "&#39;")})' class="group cursor-pointer flex flex-col rounded-2xl bg-white border border-gray-200 p-2.5 shadow-xs hover:shadow-md hover:-translate-y-0.5 transition-all">
            <div class="relative w-full aspect-[2.5/3.5] rounded-xl overflow-hidden bg-gray-50 border border-gray-100">
              <img src="${c.image_url || ""}" alt="${c.name}" loading="lazy" class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300" />
              <span class="absolute top-2 right-2 px-2 py-0.5 rounded-full bg-[#EF4444] text-white font-mono text-[10px] font-bold shadow-sm">x${c.count}</span>
              <span class="absolute bottom-2 left-2 px-2 py-0.5 rounded-md bg-[#FEF3C7]/95 text-[#92400E] font-mono text-[10px] font-bold border border-amber-200">${c.rarity}</span>
            </div>
            <div class="mt-2.5 flex flex-col gap-0.5">
              <span class="font-mono text-xs text-[#0284C7] font-bold">#${c.number}</span>
              <span class="text-sm font-bold text-gray-900 truncate">${c.name}</span>
            </div>
          </div>`;
      }
      return `
        <div class="flex flex-col justify-between rounded-2xl bg-[#F3F4F6]/80 border-2 border-dashed border-[#D1D5DB] p-2.5">
          <div class="w-full aspect-[2.5/3.5] rounded-xl bg-gray-100/80 flex flex-col items-center justify-center gap-1.5 p-2 text-center">
            <div class="w-9 h-9 rounded-full bg-white border border-gray-200 flex items-center justify-center text-gray-400">
              <span class="material-symbols-outlined text-[18px]">lock</span>
            </div>
            <span class="font-mono text-sm text-gray-500 font-bold">#${c.number}</span>
            <span class="text-xs text-gray-500 font-medium line-clamp-2">${c.name}</span>
            <span class="px-2 py-0.5 rounded-full bg-gray-200/80 text-gray-600 font-mono text-[10px]">Faltante</span>
          </div>
          <div class="mt-2.5 flex items-center justify-between font-mono text-[11px] text-gray-400">
            <span>#${c.number}</span>
            <span>${c.rarity}</span>
          </div>
        </div>`;
    })
    .join("");
}

// ---------- Dashboard ----------
async function loadStats() {
  try {
    const res = await fetch(`${API_BASE}/api/v1/stats`);
    const d = await res.json();

    document.getElementById("kpi-total-scans").textContent = d.total_scans;
    document.getElementById("kpi-success-sub").textContent = `${d.successful_scans} identificadas • ${d.failed_scans} fallidas`;
    document.getElementById("kpi-unique").textContent = d.unique_cards;
    document.getElementById("kpi-total-set").textContent = `/ ${d.total_set_cards}`;
    document.getElementById("kpi-set-badge").textContent = `${d.progress_pct}% DEL SET`;
    document.getElementById("kpi-missing-sub").textContent = `${d.total_set_cards - d.unique_cards} cartas faltantes`;
    document.getElementById("kpi-progress-pct").textContent = `${d.progress_pct}%`;
    document.getElementById("kpi-progress-bar").style.width = `${d.progress_pct}%`;
    document.getElementById("kpi-success-rate").textContent = `${d.success_rate}%`;
    document.getElementById("kpi-avg-score").textContent = `${d.avg_score}%`;

    const dupesEl = document.getElementById("dash-duplicates");
    if (!d.duplicates.length) {
      dupesEl.innerHTML = `<p class="text-sm text-gray-400 py-4 text-center">Escanea cartas para ver tus repetidas aquí.</p>`;
      return;
    }
    const maxCount = d.duplicates[0].count || 1;
    dupesEl.innerHTML = d.duplicates
      .map((item) => {
        const width = Math.round((item.count / maxCount) * 100);
        return `
          <div class="flex items-center gap-3 p-2 rounded-xl hover:bg-gray-50 transition-colors">
            <div class="w-9 h-12 rounded-lg overflow-hidden bg-gray-100 border border-gray-200 shrink-0">
              ${item.image_url ? `<img src="${item.image_url}" class="w-full h-full object-cover" />` : ""}
            </div>
            <div class="w-36 sm:w-44 shrink-0">
              <div class="text-sm font-semibold text-gray-900 truncate">${item.name}</div>
              <div class="font-mono text-[11px] font-bold text-[#0284C7]">#${item.number}</div>
            </div>
            <div class="flex-1 bg-[#E0F2FE] rounded-full h-2.5 overflow-hidden">
              <div class="h-full bg-[#38BDF8] rounded-full" style="width: ${width}%"></div>
            </div>
            <span class="px-2.5 py-0.5 rounded-full bg-red-50 text-[#EF4444] border border-red-100 font-mono text-xs font-bold shrink-0">x${item.count}</span>
          </div>`;
      })
      .join("");
  } catch (err) {
    console.error("Error cargando dashboard:", err);
  }
}

// ---------- Historial ----------
async function loadHistory() {
  try {
    const res = await fetch(`${API_BASE}/api/v1/history`);
    const d = await res.json();
    historyData = d.items || [];
    document.getElementById("hist-chip-total").textContent = `${d.total} escaneos`;
    document.getElementById("hist-chip-rate").textContent = `${d.success_rate}% éxito`;
    renderHistory();
  } catch (err) {
    console.error("Error cargando historial:", err);
  }
}

function setHistoryFilter(filter, btn) {
  historyFilter = filter;
  document.querySelectorAll(".hist-filter-btn").forEach((b) => {
    b.className = "hist-filter-btn px-3 py-1.5 rounded-full bg-gray-100 text-gray-600 hover:bg-gray-200 font-mono text-xs font-semibold";
  });
  btn.className = "hist-filter-btn px-3 py-1.5 rounded-full bg-[#EF4444] text-white font-mono text-xs font-bold";
  renderHistory();
}

function methodBadge(method) {
  if (method === "exact_number")
    return `<span class="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full bg-[#D1FAE5] text-[#065F46] font-mono text-[11px] font-bold">exact_number</span>`;
  if (method === "fuzzy_name")
    return `<span class="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full bg-[#E0F2FE] text-[#0369A1] font-mono text-[11px] font-bold">fuzzy_name</span>`;
  return `<span class="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full bg-[#FEE2E2] text-[#991B1B] font-mono text-[11px] font-bold">none</span>`;
}

function renderHistory() {
  const q = (document.getElementById("hist-search").value || "").toLowerCase().trim();
  const filtered = historyData.filter((item) => {
    if (historyFilter !== "all" && item.match_type !== historyFilter) return false;
    if (q && !item.card_name.toLowerCase().includes(q) && !item.card_number.toLowerCase().includes(q)) return false;
    return true;
  });

  const tbody = document.getElementById("hist-table-body");
  const mList = document.getElementById("hist-mobile-list");

  if (!filtered.length) {
    tbody.innerHTML = `<tr><td colspan="6" class="py-10 text-center text-gray-400 text-sm">Sin escaneos registrados.</td></tr>`;
    mList.innerHTML = `<div class="bg-white rounded-2xl p-8 text-center text-gray-400 text-sm border border-gray-200">Sin escaneos registrados.</div>`;
    return;
  }

  tbody.innerHTML = filtered
    .map(
      (item) => `
      <tr class="hover:bg-gray-50 transition-colors">
        <td class="py-3 px-4">
          <div class="flex items-center gap-3">
            <div class="w-9 h-12 rounded-md bg-gray-100 border border-gray-200 overflow-hidden shrink-0 flex items-center justify-center">
              ${item.image_url ? `<img src="${item.image_url}" class="w-full h-full object-cover" />` : `<span class="material-symbols-outlined text-gray-400 text-[18px]">broken_image</span>`}
            </div>
            <div>
              <div class="font-semibold text-gray-900">${item.card_name}</div>
              <div class="text-xs text-gray-500">${item.rarity}</div>
            </div>
          </div>
        </td>
        <td class="py-3 px-4 font-mono text-xs font-bold text-[#0284C7]">#${item.card_number}</td>
        <td class="py-3 px-4 font-mono text-xs text-gray-500">${item.scanned_at}</td>
        <td class="py-3 px-4 font-mono text-xs font-bold text-gray-800">${item.match_score}%</td>
        <td class="py-3 px-4">${methodBadge(item.match_type)}</td>
        <td class="py-3 px-4 text-right">
          <button onclick='openHistoryModal(${JSON.stringify(item).replace(/'/g, "&#39;")})' class="w-8 h-8 rounded-lg bg-gray-100 hover:bg-sky-100 text-gray-600 hover:text-[#0284C7] inline-flex items-center justify-center transition-colors">
            <span class="material-symbols-outlined text-[18px]">visibility</span>
          </button>
        </td>
      </tr>`
    )
    .join("");

  mList.innerHTML = filtered
    .map(
      (item) => `
      <article class="bg-white rounded-2xl p-3.5 border border-[#E5E7EB] shadow-xs flex items-center gap-3">
        <div class="w-12 h-16 rounded-lg bg-gray-100 border border-gray-200 overflow-hidden shrink-0 flex items-center justify-center">
          ${item.image_url ? `<img src="${item.image_url}" class="w-full h-full object-cover" />` : `<span class="material-symbols-outlined text-red-400">broken_image</span>`}
        </div>
        <div class="flex-1 min-w-0">
          <div class="flex items-center justify-between gap-2">
            <span class="font-mono text-xs font-bold text-[#0284C7]">#${item.card_number}</span>
            <span class="font-mono text-[10px] text-gray-400">${item.scanned_at}</span>
          </div>
          <div class="font-bold text-sm text-gray-900 truncate">${item.card_name}</div>
          <div class="flex items-center justify-between mt-1.5">
            ${methodBadge(item.match_type)}
            <div class="flex items-center gap-2">
              <span class="font-mono text-xs font-bold text-gray-700">${item.match_score}%</span>
              <button onclick='openHistoryModal(${JSON.stringify(item).replace(/'/g, "&#39;")})' class="w-7 h-7 rounded-lg bg-gray-100 text-gray-600 flex items-center justify-center">
                <span class="material-symbols-outlined text-[16px]">visibility</span>
              </button>
            </div>
          </div>
        </div>
      </article>`
    )
    .join("");
}

// ---------- Modales ----------
function openCardModal(card) {
  document.getElementById("modal-sub").textContent = `Carta #${card.number} • ${card.rarity}`;
  document.getElementById("modal-title").textContent = card.name;
  document.getElementById("modal-img").src = card.image_url || "";
  document.getElementById("modal-meta").innerHTML = `
    <div class="flex justify-between"><span>ID Set:</span><strong>${card.id}</strong></div>
    <div class="flex justify-between"><span>Copias en colección:</span><strong>x${card.count}</strong></div>
  `;
  document.getElementById("detail-modal").classList.remove("hidden");
}

function openHistoryModal(item) {
  document.getElementById("modal-sub").textContent = `Escaneo #${item.id} • ${item.scanned_at}`;
  document.getElementById("modal-title").textContent = item.card_name;
  document.getElementById("modal-img").src = item.uploaded_image ? `${API_BASE}${item.uploaded_image}` : item.image_url || "";
  document.getElementById("modal-meta").innerHTML = `
    <div class="flex justify-between"><span>Número:</span><strong>#${item.card_number}</strong></div>
    <div class="flex justify-between"><span>Método:</span><strong>${item.match_type}</strong></div>
    <div class="flex justify-between"><span>Precisión:</span><strong>${item.match_score}%</strong></div>
  `;
  document.getElementById("detail-modal").classList.remove("hidden");
}

function closeModal() {
  document.getElementById("detail-modal").classList.add("hidden");
}

function refreshAllData() {
  loadCollection();
  loadStats();
  loadHistory();
}

// Inicialización
switchView("escaner");