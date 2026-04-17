import express from 'express';
import fetch, { Headers } from 'node-fetch';
import cors from 'cors';
import dotenv from 'dotenv';

dotenv.config();

// قائمة النطاقات المسموحة، افصلها بفواصل
const ALLOWED = (process.env.ALLOWED_HOSTS || 'api.fustog.app')
  .split(',')
  .map((s) => s.trim().toLowerCase())
  .filter(Boolean);
const PORT = Number(process.env.PORT || 8787);

const app = express();
app.use(cors());
app.use(express.text({ type: 'text/*', limit: '5mb' }));
app.use(express.json({ limit: '5mb' }));

function ensureAllowed(targetUrl: string) {
  let host = '';
  try { host = new URL(targetUrl).host.toLowerCase(); } catch { /* ignore */ }
  if (!host || !ALLOWED.includes(host)) {
    throw new Error(`Host not allowed: ${host}`);
  }
}

// --- بث مباشر عبر SSE ---
type Client = { id: number; res: express.Response };
let clients: Client[] = [];
let nextId = 1;
const recent: any[] = [];

app.get('/stream', (req, res) => {
  res.setHeader('Content-Type', 'text/event-stream');
  res.setHeader('Cache-Control', 'no-cache');
  res.setHeader('Connection', 'keep-alive');
  res.flushHeaders?.();
  const id = nextId++;
  clients.push({ id, res });
  // أرسل آخر العناصر كسجل ابتدائي صغير
  for (const r of recent.slice(-50)) {
    res.write(`event: entry\ndata: ${JSON.stringify(r)}\n\n`);
  }
  req.on('close', () => {
    clients = clients.filter((c) => c.id !== id);
  });
});

function broadcast(entry: any) {
  recent.push(entry);
  if (recent.length > 500) recent.shift();
  const data = `event: entry\ndata: ${JSON.stringify(entry)}\n\n`;
  for (const c of clients) {
    c.res.write(data);
  }
}

// يستقبل إدخالات JSON (عنصر واحد أو مصفوفة) من البروكسي/الإضافة
app.post('/ingest', (req, res) => {
  const payload = req.body;
  if (!payload) return res.status(400).json({ code: 'bad_request', message: 'empty body' });
  const list = Array.isArray(payload) ? payload : [payload];
  for (const e of list) broadcast(e);
  res.json({ ok: true, received: list.length });
});

app.all('/relay', async (req, res) => {
  try {
    const target = String(req.query.url || '');
    ensureAllowed(target);
    const hdrs = new Headers();
    for (const [k, v] of Object.entries(req.headers)) {
      if (!v) continue;
      if (Array.isArray(v)) hdrs.set(k, v.join(','));
      else hdrs.set(k, String(v));
    }
    // لا نمرر هيدر المضيف والاتصال الداخلي
    hdrs.delete('host');
    hdrs.delete('connection');
    const init: any = { method: req.method, headers: hdrs };
    if (!['GET', 'HEAD'].includes(req.method)) {
      init.body = req.body;
    }
    const r = await fetch(target, init);
    const text = await r.text();
    res.status(r.status);
    r.headers.forEach((v, k) => res.setHeader(k, v));
    res.send(text);
  } catch (e) {
    res
      .status(400)
      .json({ code: 'relay_error', message: (e as Error).message });
  }
});

app.get('/health', (_req, res) => res.json({ ok: true }));

app.listen(PORT, () => {
  // eslint-disable-next-line no-console
  console.log(`Relay listening on http://localhost:${PORT} (allowed: ${ALLOWED.join(', ')})`);
});


