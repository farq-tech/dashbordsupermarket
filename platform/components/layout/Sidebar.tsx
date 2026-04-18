'use client'

import { SidebarPanel } from './SidebarPanel'
import { MobileNavDrawer } from './MobileNavDrawer'

export function Sidebar() {
  return (
    <>
      <aside
        className="sticky top-0 hidden h-screen w-64 shrink-0 flex-col md:flex"
        style={{
          background: 'var(--color-sidebar-bg)',
          borderInlineStart: '1px solid var(--color-border)',
        }}
      >
        <SidebarPanel variant="desktop" />
      </aside>
      <MobileNavDrawer />
    </>
  )
}
