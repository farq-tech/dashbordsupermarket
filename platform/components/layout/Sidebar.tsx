'use client'

import { SidebarPanel } from './SidebarPanel'
import { MobileNavDrawer } from './MobileNavDrawer'
import { cn } from '@/components/ui/cn'

export function Sidebar({ hidden }: { hidden?: boolean }) {
  return (
    <>
      <aside
        className={cn(
          'print:hidden sticky z-20 hidden h-screen w-64 shrink-0 flex-col md:flex',
          'md:h-[calc(100vh-1.5rem)] md:max-h-[calc(100vh-1.5rem)] md:self-start md:top-3',
          'md:rounded-[var(--radius-lg)] md:border md:border-[var(--color-border)] md:shadow-[var(--shadow-tile)] md:m-3',
          hidden && 'md:hidden',
        )}
        style={{
          background: 'var(--color-sidebar-bg)',
        }}
      >
        <SidebarPanel variant="desktop" />
      </aside>
      <MobileNavDrawer />
    </>
  )
}
