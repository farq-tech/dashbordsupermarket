import { Sidebar } from '@/components/layout/Sidebar'
import { DataProvider } from '@/components/layout/DataProvider'

export default function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <DataProvider>
      <div
        className="flex min-h-screen w-full flex-col md:flex-row-reverse"
        style={{ background: 'var(--color-bg)' }}
      >
        <Sidebar />
        <main className="min-w-0 flex-1 overflow-x-hidden pb-[env(safe-area-inset-bottom,0px)]">
          <div className="w-full max-w-screen-2xl mx-auto">
            {children}
          </div>
        </main>
      </div>
    </DataProvider>
  )
}
