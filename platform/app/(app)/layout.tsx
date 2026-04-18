import { Sidebar } from '@/components/layout/Sidebar'
import { DataProvider } from '@/components/layout/DataProvider'

export default function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <DataProvider>
      <div className="min-h-screen" style={{ background: 'var(--color-bg)' }}>
        <Sidebar />
        <main className="min-h-screen w-full min-w-0 md:mr-64 pb-[env(safe-area-inset-bottom,0px)]">
          {children}
        </main>
      </div>
    </DataProvider>
  )
}
