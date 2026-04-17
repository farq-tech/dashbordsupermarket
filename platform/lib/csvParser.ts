/**
 * Minimal CSV parser for server-side use (no external deps).
 * Handles quoted fields, escaped quotes, and optional trailing newlines.
 */
export function parseCsv(text: string): Record<string, string>[] {
  const lines = text.replace(/\r\n/g, '\n').replace(/\r/g, '\n').split('\n')
  if (lines.length === 0) return []

  const headers = parseRow(lines[0])
  const results: Record<string, string>[] = []

  for (let i = 1; i < lines.length; i++) {
    const line = lines[i].trim()
    if (!line) continue
    const values = parseRow(line)
    const obj: Record<string, string> = {}
    headers.forEach((h, idx) => {
      obj[h] = values[idx] ?? ''
    })
    results.push(obj)
  }

  return results
}

function parseRow(line: string): string[] {
  const fields: string[] = []
  let current = ''
  let inQuotes = false

  for (let i = 0; i < line.length; i++) {
    const ch = line[i]
    if (ch === '"') {
      if (inQuotes && line[i + 1] === '"') {
        current += '"'
        i++
      } else {
        inQuotes = !inQuotes
      }
    } else if (ch === ',' && !inQuotes) {
      fields.push(current)
      current = ''
    } else {
      current += ch
    }
  }
  fields.push(current)
  return fields
}

export function num(v: string | undefined): number {
  if (v === undefined || v === null || v === '') return 0
  const n = parseFloat(v)
  return isNaN(n) ? 0 : n
}

export function int(v: string | undefined): number {
  if (v === undefined || v === null || v === '') return 0
  const n = parseInt(v, 10)
  return isNaN(n) ? 0 : n
}
