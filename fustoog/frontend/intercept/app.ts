/* 
  Intercept Viewer & Replayer core logic
  ملاحظات بالعربية: الكود يعمل محليًا في المتصفح. لا يتم إرسال أي بيانات لخوادم خارجية.
*/

type HeaderMap = Record<string, string>;

export type NormalizedEntry = {
  ts: number;
  method: string;
  url: string;
  status: number | null;
  reqHeaders: HeaderMap;
  resHeaders: HeaderMap;
  reqBody?: string;
  resBody?: string;
  size?: number;
};

// ترجمة بسيطة بنصوص إنجليزية، مع دعم عربي داخل التلميحات
const t = (key: string) => {
  const map: Record<string, string> = {
    'ui.no_data': 'No data loaded yet.',
    'ui.copy': 'Copy',
    'ui.copied': 'Copied',
  };
  return map[key] ?? key;
};

const state = {
  entries: [] as NormalizedEntry[],
  filtered: [] as NormalizedEntry[],
  redact: true,
  selectedIndex: -1,
};

const qs = <T extends HTMLElement>(sel: string) =>
  document.querySelector(sel) as T;

const fileInput = qs<HTMLInputElement>('#file-input');
const pasteArea = qs<HTMLTextAreaElement>('#paste-area');
const parsePasteBtn = qs<HTMLButtonElement>('#parse-paste');
const pasteBtn = qs<HTMLButtonElement>('#paste-button');
const tbody = qs<HTMLTableSectionElement>('#req-tbody');
const empty = qs<HTMLDivElement>('#empty-state');
const rtlToggle = qs<HTMLInputElement>('#rtl-toggle');
const redactToggle = qs<HTMLInputElement>('#redact-toggle');
const liveToggle = qs<HTMLInputElement>('#live-toggle');
const liveUrl = qs<HTMLInputElement>('#live-url');
const methodFilter = qs<HTMLSelectElement>('#method-filter');
const hostFilter = qs<HTMLInputElement>('#host-filter');
const statusFilter = qs<HTMLInputElement>('#status-filter');
const searchFilter = qs<HTMLInputElement>('#search-filter');
const tokensList = qs<HTMLUListElement>('#tokens-list');
const exportJSONBtn = qs<HTMLButtonElement>('#export-json');
const exportCSVBtn = qs<HTMLButtonElement>('#export-csv');
const testLiveBtn = qs<HTMLButtonElement>('#test-live');
const decodeInput = qs<HTMLTextAreaElement>('#decode-input');
const decodeBtn = qs<HTMLButtonElement>('#decode-btn');
const decodeClearBtn = qs<HTMLButtonElement>('#decode-clear');
const decodeOutput = qs<HTMLTextAreaElement>('#decode-output');

// Details
const detailUrl = qs<HTMLInputElement>('#detail-url');
const detailMethod = qs<HTMLSelectElement>('#detail-method');
const detailReqHeaders = qs<HTMLTextAreaElement>('#detail-req-headers');
const detailReqBody = qs<HTMLTextAreaElement>('#detail-req-body');
const detailStatus = qs<HTMLInputElement>('#detail-status');
const detailResHeaders = qs<HTMLTextAreaElement>('#detail-res-headers');
const detailResBody = qs<HTMLTextAreaElement>('#detail-res-body');
const replayBtn = qs<HTMLButtonElement>('#replay-btn');
const replayTarget = qs<HTMLSelectElement>('#replay-target');

// Token detection
const TOKEN_HEADER = /^(authorization|x[-_]?api[-_]?key|x[-_]?access[-_]?token|api[-_]?key)$/i;
const BEARER_RE = /bearer\\s+([A-Za-z0-9-_.]+)/i;
const COOKIE_TOKEN = /(session|auth|token|jwt)/i;

function normalizeHeaders(headers: Array<{ name: string; value: string }> | HeaderMap | undefined): HeaderMap {
  if (!headers) return {};
  if (Array.isArray(headers)) {
    const o: HeaderMap = {};
    for (const h of headers) {
      if (!h || !h.name) continue;
      o[h.name.toLowerCase()] = String(h.value ?? '');
    }
    return o;
  }
  const o: HeaderMap = {};
  for (const k of Object.keys(headers)) {
    o[k.toLowerCase()] = String((headers as HeaderMap)[k] ?? '');
  }
  return o;
}

function tryBase64DecodeIfLooksEncoded(text?: string, resHeaders?: HeaderMap): string | undefined {
  if (!text) return text;
  const contentType = resHeaders?.['content-type'] ?? '';
  // إذا كان النص يبدو base64 أو تم إرساله كنص عادي لكنه مُرمّز
  const looksB64 = /^[A-Za-z0-9+/\\r\\n]+={0,2}$/.test(text.trim()) && text.length > 32;
  if (!looksB64) return text;
  try {
    const decoded = atob(text.replace(/\\s+/g, ''));
    // تحقق سريع أن الناتج نصّي
    if (/[\\x00-\\x08]/.test(decoded)) return text;
    // إذا المحتوى JSON نحاول تهيئته
    if (/json|javascript/.test(contentType)) {
      try {
        return JSON.stringify(JSON.parse(decoded), null, 2);
      } catch {
        return decoded;
      }
    }
    return decoded;
  } catch {
    return text;
  }
}

function parseHAR(json: any): NormalizedEntry[] {
  if (!json?.log?.entries) return [];
  const out: NormalizedEntry[] = [];
  for (const e of json.log.entries) {
    const req = e.request ?? {};
    const res = e.response ?? {};
    const ts = e.startedDateTime ? Date.parse(e.startedDateTime) : Date.now();
    const url: string = req.url ?? '';
    const method: string = req.method ?? 'GET';
    const status: number | null = typeof res.status === 'number' ? res.status : null;
    const reqHeaders = normalizeHeaders(req.headers);
    const resHeaders = normalizeHeaders(res.headers);
    let reqBody = '';
    let resBody = '';
    if (req.postData?.text) reqBody = String(req.postData.text);
    if (res.content?.text) resBody = String(res.content.text);
    const size = res.bodySize ?? res.content?.size ?? undefined;
    out.push({
      ts,
      method,
      url,
      status,
      reqHeaders,
      resHeaders,
      reqBody,
      resBody: tryBase64DecodeIfLooksEncoded(resBody, resHeaders) ?? resBody,
      size,
    });
  }
  return out;
}

function parseJSONLines(text: string): NormalizedEntry[] {
  const out: NormalizedEntry[] = [];
  for (const line of text.split(/\\r?\\n/)) {
    const l = line.trim();
    if (!l) continue;
    try {
      const j = JSON.parse(l);
      out.push(...normalizeGeneric(j));
    } catch {
      // ignore
    }
  }
  return out;
}

function normalizeGeneric(json: any): NormalizedEntry[] {
  // محاولة تطبيع بنية عامة
  const guessArray = Array.isArray(json) ? json : [json];
  const out: NormalizedEntry[] = [];
  for (const e of guessArray) {
    if (!e) continue;
    const ts = e.ts ?? e.time ?? Date.now();
    const method = (e.method ?? e.req?.method ?? 'GET').toUpperCase();
    const url = e.url ?? e.req?.url ?? '';
    const status = e.status ?? e.res?.status ?? null;
    const reqHeaders = normalizeHeaders(e.reqHeaders ?? e.req?.headers);
    const resHeaders = normalizeHeaders(e.resHeaders ?? e.res?.headers);
    const reqBody = e.reqBody ?? e.req?.body ?? '';
    const resBodyRaw = e.resBody ?? e.res?.body ?? '';
    const resBody = tryBase64DecodeIfLooksEncoded(resBodyRaw, resHeaders) ?? resBodyRaw;
    const size = e.size ?? undefined;
    out.push({ ts, method, url, status, reqHeaders, resHeaders, reqBody, resBody, size });
  }
  return out;
}

function detectTokens(entries: NormalizedEntry[]): Array<{ source: string; key: string; value: string }> {
  const found: Array<{ source: string; key: string; value: string }> = [];
  for (const e of entries) {
    for (const [k, v] of Object.entries(e.reqHeaders)) {
      if (TOKEN_HEADER.test(k) || BEARER_RE.test(v)) {
        found.push({ source: e.url, key: k, value: v });
      }
      if (k === 'cookie') {
        const parts = v.split(/;\\s*/);
        for (const p of parts) {
          const [ck, cv] = p.split('=');
          if (COOKIE_TOKEN.test(ck)) {
            found.push({ source: e.url, key: `cookie:${ck}`, value: cv ?? '' });
          }
        }
      }
    }
  }
  return found;
}

function formatBytes(n?: number | null): string {
  if (!n && n !== 0) return '';
  const units = ['B', 'KB', 'MB', 'GB'];
  let x = n as number, i = 0;
  while (x >= 1024 && i < units.length - 1) { x /= 1024; i++; }
  return `${x.toFixed(1)} ${units[i]}`;
}

function hostFromUrl(u: string): string {
  try { return new URL(u).host; } catch { return ''; }
}
function pathFromUrl(u: string): string {
  try { const x = new URL(u); return x.pathname + (x.search || ''); } catch { return u; }
}

function applyFilters() {
  const m = methodFilter.value;
  const h = hostFilter.value.toLowerCase();
  const s = statusFilter.value.trim();
  const q = searchFilter.value.toLowerCase();
  state.filtered = state.entries.filter((e) => {
    if (m && e.method !== m) return false;
    if (h && !hostFromUrl(e.url).toLowerCase().includes(h)) return false;
    if (s && String(e.status ?? '').indexOf(s) === -1) return false;
    if (q) {
      const blob = [e.url, JSON.stringify(e.reqHeaders), JSON.stringify(e.resHeaders), e.reqBody ?? '', e.resBody ?? ''].join('\\n').toLowerCase();
      if (!blob.includes(q)) return false;
    }
    return true;
  });
  renderTable();
  renderTokens();
}

function renderTable() {
  tbody.innerHTML = '';
  if (!state.filtered.length) {
    empty.textContent = t('ui.no_data');
    empty.style.display = 'block';
    return;
  }
  empty.style.display = 'none';
  for (const [i, e] of state.filtered.entries()) {
    const tr = document.createElement('tr');
    tr.className = 'req-row';
    tr.innerHTML = `
      <td>${new Date(e.ts).toLocaleTimeString()}</td>
      <td>${e.method}</td>
      <td>${e.status ?? ''}</td>
      <td>${hostFromUrl(e.url)}</td>
      <td title="${e.url}">${pathFromUrl(e.url)}</td>
      <td>${formatBytes(e.size)}</td>
    `;
    tr.addEventListener('click', () => selectRow(i));
    tbody.appendChild(tr);
  }
}

function redactSecrets(v: string): string {
  if (!state.redact) return v;
  if (!v) return v;
  // إخفاء القيم الطويلة المحتملة للأسرار
  if (v.length > 16) return v.slice(0, 6) + '••••••' + v.slice(-4);
  return '••••';
}

function renderTokens() {
  tokensList.innerHTML = '';
  const toks = detectTokens(state.filtered);
  for (const tkn of toks) {
    const li = document.createElement('li');
    li.className = 'token-item';
    const value = state.redact ? redactSecrets(tkn.value) : tkn.value;
    li.innerHTML = `
      <div>
        <div><strong>${tkn.key}</strong></div>
        <small>${tkn.source}</small>
      </div>
      <div>
        <code>${value}</code>
      </div>
    `;
    tokensList.appendChild(li);
  }
}

function selectRow(filteredIndex: number) {
  state.selectedIndex = filteredIndex;
  const e = state.filtered[filteredIndex];
  if (!e) return;
  detailUrl.value = e.url;
  detailMethod.value = e.method;
  detailReqHeaders.value = JSON.stringify(e.reqHeaders, null, 2);
  detailReqBody.value = e.reqBody ?? '';
  detailStatus.value = String(e.status ?? '');
  detailResHeaders.value = JSON.stringify(e.resHeaders, null, 2);
  detailResBody.value = (e.resBody ?? '');
}

async function loadFile(f: File) {
  const text = await f.text();
  parseText(text);
}

function parseText(text: string) {
  let json: any | undefined;
  try { json = JSON.parse(text); } catch { /* not single JSON */ }
  let entries: NormalizedEntry[] = [];
  if (json?.log?.entries) {
    entries = parseHAR(json);
  } else if (json) {
    entries = normalizeGeneric(json);
  } else {
    entries = parseJSONLines(text);
  }
  if (!entries.length) {
    alert('Unable to parse file. تأكد من أن الصيغة HAR أو JSON.');
    return;
  }
  state.entries = entries;
  state.filtered = entries.slice();
  renderTable();
  renderTokens();
}

// Live streaming (SSE)
let es: EventSource | null = null;
function startLive() {
  stopLive();
  try {
    es = new EventSource(liveUrl.value);
    es.addEventListener('entry', (ev: MessageEvent) => {
      try {
        const data = JSON.parse(ev.data);
        const normalized = normalizeGeneric(data);
        if (!normalized.length) return;
        state.entries.push(...normalized);
        // إبقاء الأداء: لا تتجاوز 5000 عنصر
        if (state.entries.length > 5000) state.entries.splice(0, state.entries.length - 5000);
        applyFilters();
      } catch { /* ignore malformed */ }
    });
    es.onerror = () => {
      // إعادة المحاولة لاحقًا يعتمد على EventSource تلقائيًا
    };
  } catch (e) {
    alert('Live stream failed: ' + (e as Error).message);
  }
}
function stopLive() {
  if (es) { es.close(); es = null; }
}

async function decodeBase64Local() {
  const raw = (decodeInput.value || '').trim();
  if (!raw) { decodeOutput.value = ''; return; }
  try {
    // فك Base64 أولاً
    const bin = Uint8Array.from(atob(raw.replace(/\s+/g, '')), c => c.charCodeAt(0));
    
    // محاولة فك Gzip/Deflate إذا كان موجودًا
    let decompressed: Uint8Array | null = null;
    if (typeof CompressionStream !== 'undefined') {
      try {
        const stream = new DecompressionStream('gzip');
        const writer = stream.writable.getWriter();
        writer.write(bin);
        writer.close();
        const reader = stream.readable.getReader();
        const chunks: Uint8Array[] = [];
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          chunks.push(value);
        }
        if (chunks.length > 0) {
          const totalLen = chunks.reduce((a, b) => a + b.length, 0);
          decompressed = new Uint8Array(totalLen);
          let offset = 0;
          for (const chunk of chunks) {
            decompressed.set(chunk, offset);
            offset += chunk.length;
          }
        }
      } catch {
        // إذا فشل Gzip، جرب Deflate
        try {
          const stream = new DecompressionStream('deflate');
          const writer = stream.writable.getWriter();
          writer.write(bin);
          writer.close();
          const reader = stream.readable.getReader();
          const chunks: Uint8Array[] = [];
          while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            chunks.push(value);
          }
          if (chunks.length > 0) {
            const totalLen = chunks.reduce((a, b) => a + b.length, 0);
            decompressed = new Uint8Array(totalLen);
            let offset = 0;
            for (const chunk of chunks) {
              decompressed.set(chunk, offset);
              offset += chunk.length;
            }
          }
        } catch {
          // ليس مضغوطًا، استخدم البيانات الأصلية
        }
      }
    }
    
    const finalBin = decompressed || bin;
    const txt = new TextDecoder('utf-8', { fatal: false }).decode(finalBin);
    
    // محاولة تهيئة JSON
    try {
      decodeOutput.value = JSON.stringify(JSON.parse(txt), null, 2);
    } catch {
      decodeOutput.value = txt || '(فك التشفير نجح لكن النص فارغ أو غير نصي)';
    }
  } catch (e) {
    decodeOutput.value = 'خطأ في فك التشفير: ' + (e as Error).message + '\n\nتأكد أن النص Base64 صحيح.';
  }
}

// Exporters (CSV/JSON) — CSV implemented in utils/csv.ts
async function exportJSON() {
  const data = state.filtered.map(safeEntryForExport);
  downloadBlob(JSON.stringify(data, null, 2), 'intercepts.json', 'application/json');
}

async function exportCSV() {
  const { toCSV } = await import('../utils/csv.ts');
  const rows = state.filtered.map((e) => ({
    ts: new Date(e.ts).toISOString(),
    method: e.method,
    url: e.url,
    status: e.status ?? '',
    size: e.size ?? '',
    req_headers: JSON.stringify(safeHeaders(e.reqHeaders)),
    res_headers: JSON.stringify(e.resHeaders),
  }));
  const csv = toCSV(rows);
  downloadBlob(csv, 'intercepts.csv', 'text/csv');
}

function safeHeaders(h: HeaderMap): HeaderMap {
  const o: HeaderMap = {};
  for (const [k, v] of Object.entries(h)) {
    if (TOKEN_HEADER.test(k) || BEARER_RE.test(v) || k === 'cookie') {
      o[k] = state.redact ? redactSecrets(v) : v;
    } else {
      o[k] = v;
    }
  }
  return o;
}

function safeEntryForExport(e: NormalizedEntry): NormalizedEntry {
  return {
    ...e,
    reqHeaders: safeHeaders(e.reqHeaders),
    // لا نصدّر الأجسام إلا إذا كانت ليست أسرار—نحتفظ بها كما هي لأنها مفيدة للفحص
  };
}

function downloadBlob(content: string, filename: string, mime: string) {
  const blob = new Blob([content], { type: mime });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = filename;
  a.click();
  URL.revokeObjectURL(a.href);
}

async function replay() {
  const url = detailUrl.value;
  const method = detailMethod.value;
  let headers: HeaderMap = {};
  try { headers = JSON.parse(detailReqHeaders.value || '{}'); } catch {
    alert('Request headers must be valid JSON');
    return;
  }
  const body = ['GET', 'HEAD'].includes(method) ? undefined : (detailReqBody.value || undefined);
  const target = replayTarget.value;
  try {
    let finalUrl = url;
    let init: RequestInit = { method, headers, body };
    if (target === 'relay') {
      // نرسل عبر ريلاي محلي لتفادي CORS
      finalUrl = `/relay?url=${encodeURIComponent(url)}`;
      init = { method, headers, body };
    }
    const res = await fetch(finalUrl, init);
    const text = await res.text();
    detailStatus.value = `${res.status}`;
    detailResHeaders.value = Array.from(res.headers.entries()).map(([k, v]) => `${k}: ${v}`).join('\\n');
    // محاولة تحويل JSON
    try { detailResBody.value = JSON.stringify(JSON.parse(text), null, 2); }
    catch { detailResBody.value = text; }
    alert('Replay done.');
  } catch (e) {
    console.error(e);
    alert('Replay failed: ' + (e as Error).message);
  }
}

// Event wiring
fileInput.addEventListener('change', () => {
  const f = fileInput.files?.[0];
  if (f) loadFile(f);
});
pasteBtn.addEventListener('click', async () => {
  try {
    const text = await navigator.clipboard.readText();
    pasteArea.value = text;
  } catch {
    alert('Clipboard read failed. الرجاء اللصق يدويًا.');
  }
});
parsePasteBtn.addEventListener('click', () => parseText(pasteArea.value));

rtlToggle.addEventListener('change', () => {
  document.documentElement.setAttribute('dir', rtlToggle.checked ? 'rtl' : 'ltr');
});
redactToggle.addEventListener('change', () => {
  state.redact = redactToggle.checked;
  renderTokens();
});
methodFilter.addEventListener('change', applyFilters);
hostFilter.addEventListener('input', applyFilters);
statusFilter.addEventListener('input', applyFilters);
searchFilter.addEventListener('input', applyFilters);
exportJSONBtn.addEventListener('click', exportJSON);
exportCSVBtn.addEventListener('click', exportCSV);
replayBtn.addEventListener('click', replay);
liveToggle.addEventListener('change', () => {
  if (liveToggle.checked) startLive();
  else stopLive();
});
testLiveBtn.addEventListener('click', async () => {
  // إرسال عنصر اختبار إلى /ingest للتحقق من البث
  const sample: NormalizedEntry = {
    ts: Date.now(),
    method: 'GET',
    url: 'https://example.test/health?via=test-live',
    status: 200,
    reqHeaders: { 'x-test': 'live' },
    resHeaders: { 'content-type': 'application/json' },
    reqBody: '',
    resBody: JSON.stringify({ ok: true, source: 'test-live' }),
    size: 24,
  };
  try {
    await fetch('http://localhost:8787/ingest', {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify(sample),
    });
    alert('Test entry sent to /ingest. يجب أن يظهر فورًا.');
  } catch (e) {
    alert('Failed to send test entry: ' + (e as Error).message);
  }
});

decodeBtn.addEventListener('click', decodeBase64Local);
decodeClearBtn.addEventListener('click', () => { decodeInput.value = ''; decodeOutput.value = ''; });
decodeInput.addEventListener('keydown', (e) => { if (e.ctrlKey && e.key.toLowerCase() === 'enter') decodeBase64Local(); });

// حالة بدئية
empty.textContent = t('ui.no_data');


