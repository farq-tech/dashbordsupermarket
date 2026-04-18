'use client'

import { SidebarPanel } from './SidebarPanel'
import { MobileNavDrawer } from './MobileNavDrawer'

export function Sidebar() {
  return (
    <>
      <aside
        className="hidden md:flex fixed top-0 right-0 z-40 h-screen w-64 flex-col"
        style={{
          background: 'var(--color-sidebar-bg)',
          borderLeft: '1px solid var(--color-border)',
        }}
      >
        <SidebarPanel variant="desktop" />
      </aside>
      <MobileNavDrawer />
    </>
  )
}
