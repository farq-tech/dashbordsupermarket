import type { DecisionBrief } from './types'

/** Minimal HTML report for download; open in browser or print to PDF. */
export function buildDecisionBriefHtml(brief: DecisionBrief, lang: 'ar' | 'en'): string {
  const isAr = lang === 'ar'
  const title = isAr ? 'تقرير مركز القرار' : 'Decision Center Report'
  const rows = brief.queue
    .map(
      (item, i) => `
    <tr>
      <td>${i + 1}</td>
      <td>${escapeHtml(isAr ? item.title_ar : item.title_en)}</td>
      <td>${item.score}</td>
      <td>${item.kind}</td>
      <td>${escapeHtml(isAr ? item.context_ar : item.context_en).slice(0, 200)}</td>
    </tr>`,
    )
    .join('')

  return `<!DOCTYPE html>
<html lang="${lang}" dir="${isAr ? 'rtl' : 'ltr'}">
<head>
  <meta charset="utf-8"/>
  <title>${title}</title>
  <style>
    body { font-family: system-ui, sans-serif; margin: 24px; color: #1f2937; }
    h1 { font-size: 1.25rem; }
    table { border-collapse: collapse; width: 100%; margin-top: 16px; font-size: 12px; }
    th, td { border: 1px solid #e5e7eb; padding: 8px; text-align: ${isAr ? 'right' : 'left'}; vertical-align: top; }
    th { background: #f9fafb; }
    .meta { color: #6b7280; font-size: 13px; margin: 8px 0; }
  </style>
</head>
<body>
  <h1>${title}</h1>
  <p class="meta">${escapeHtml(isAr ? brief.headline_ar : brief.headline_en)}</p>
  <p class="meta">${escapeHtml(isAr ? brief.subline_ar : brief.subline_en)}</p>
  <p class="meta">${isAr ? 'التاريخ' : 'As of'}: ${escapeHtml(brief.data_as_of)}</p>
  <table>
    <thead><tr><th>#</th><th>${isAr ? 'العنوان' : 'Title'}</th><th>score</th><th>kind</th><th>${isAr ? 'تفاصيل' : 'Detail'}</th></tr></thead>
    <tbody>${rows}</tbody>
  </table>
</body>
</html>`
}

function escapeHtml(s: string) {
  return s
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
}

export function downloadHtmlFile(html: string, filename: string) {
  const blob = new Blob([html], { type: 'text/html;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}
