 'use client'

import { Sidebar } from '@/components/layout/Sidebar'
import { DataProvider } from '@/components/layout/DataProvider'
import { useAppStore } from '@/store/useAppStore'

export default function AppLayout({ children }: { children: React.ReactNode }) {
  const { lang, desktopSidebarHidden } = useAppStore()
  const sidebarSide: 'right' | 'left' = lang === 'ar' ? 'right' : 'left'

  return (
    <DataProvider>
      <div
        className={`flex min-h-screen w-full flex-col md:flex-row ${lang === 'ar' ? 'md:flex-row-reverse' : ''}`}
        style={{ background: 'var(--color-bg)' }}
      >
        <Sidebar hidden={desktopSidebarHidden} side={sidebarSide} />
        <main className="min-w-0 flex-1 overflow-x-hidden pb-[env(safe-area-inset-bottom,0px)]">
          <div className="w-full max-w-screen-2xl mx-auto">
            {children}
          </div>
        </main>
      </div>
    </DataProvider>
  )
}
