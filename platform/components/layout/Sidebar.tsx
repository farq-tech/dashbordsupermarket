'use client'

import { SidebarPanel } from './SidebarPanel'
import { MobileNavDrawer } from './MobileNavDrawer'
import { cn } from '@/components/ui/cn'

export function Sidebar({ hidden, side }: { hidden?: boolean; side: 'right' | 'left' }) {
  return (
    <>
      <aside
        className={cn(
          'sticky top-0 hidden h-screen w-64 shrink-0 flex-col md:flex',
          hidden && 'md:hidden',
        )}
        style={{
          background: 'var(--color-sidebar-bg)',
          borderLeft: side === 'right' ? '1px solid var(--color-border)' : undefined,
          borderRight: side === 'left' ? '1px solid var(--color-border)' : undefined,
        }}
      >
        <SidebarPanel variant="desktop" />
      </aside>
      <MobileNavDrawer />
    </>
  )
}
