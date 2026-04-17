import { Sidebar } from '@/components/layout/Sidebar'
import { DataProvider } from '@/components/layout/DataProvider'

export default function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <DataProvider>
      <div className="min-h-screen" style={{ background: 'var(--color-bg)' }}>
        <Sidebar />
        <main className="mr-60 min-h-screen">
          {children}
        </main>
      </div>
    </DataProvider>
  )
}
