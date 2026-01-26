export function toCSV(rows) {
  if (!rows.length) return '';
  const headers = Object.keys(rows[0]);
  const esc = (v) => {
    const s = v === null || v === undefined ? '' : String(v);
    const needs = /[",\n\r]/.test(s);
    if (!needs) return s;
    return '"' + s.replace(/"/g, '""') + '"';
    };
  const lines = [
    headers.map(esc).join(','),
    ...rows.map((r) => headers.map((h) => esc(r[h])).join(',')),
  ];
  return lines.join('\r\n');
}


