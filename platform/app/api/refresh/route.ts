import { NextResponse } from 'next/server'
import { invalidateCache, getDataBundle, getCacheInfo } from '@/lib/dataCache'

export const dynamic = 'force-dynamic'

export async function POST() {
  try {
    invalidateCache()
    await getDataBundle()
    const info = getCacheInfo()
    return NextResponse.json({ success: true, message: 'Data refreshed successfully', ...info })
  } catch (error) {
    console.error('[API/refresh] Error:', error)
    return NextResponse.json({ error: 'Refresh failed' }, { status: 500 })
  }
}
