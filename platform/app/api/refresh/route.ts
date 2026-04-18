import { NextResponse } from 'next/server'
import { invalidateCache, getDataBundle, getCacheInfo } from '@/lib/dataCache'

export const dynamic = 'force-dynamic'

function parseSource(raw: string | null): 'restaurants' | 'supermarket' {
  if (raw === 'supermarket' || raw === 'restaurants') return raw
  return 'restaurants'
}

export async function POST(request: Request) {
  try {
    const url = new URL(request.url)
    const source = parseSource(url.searchParams.get('source'))
    invalidateCache(source)
    await getDataBundle(source)
    const info = getCacheInfo(source)
    return NextResponse.json({ success: true, message: 'Data refreshed successfully', ...info })
  } catch (error) {
    console.error('[API/refresh] Error:', error)
    return NextResponse.json({ error: 'Refresh failed' }, { status: 500 })
  }
}
