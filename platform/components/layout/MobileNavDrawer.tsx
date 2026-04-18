'use client'

import * as Dialog from '@radix-ui/react-dialog'
import { X } from 'lucide-react'
import { useAppStore } from '@/store/useAppStore'
import { SidebarPanel } from './SidebarPanel'

export function MobileNavDrawer() {
  const mobileNavOpen = useAppStore(s => s.mobileNavOpen)
  const setMobileNavOpen = useAppStore(s => s.setMobileNavOpen)
  const lang = useAppStore(s => s.lang)

  return (
    <Dialog.Root open={mobileNavOpen} onOpenChange={setMobileNavOpen}>
      <Dialog.Portal>
        <Dialog.Overlay
          className="fixed inset-0 z-[60] bg-black/45 backdrop-blur-[1px] md:hidden"
          style={{ paddingTop: 'env(safe-area-inset-top, 0px)' }}
        />
        <Dialog.Content
          className="fixed inset-y-0 z-[61] flex w-[min(20rem,100vw)] max-w-full flex-col bg-[var(--color-sidebar-bg)] shadow-xl outline-none transition-transform duration-200 md:hidden"
          style={{
            right: 0,
            left: 'auto',
            borderLeft: '1px solid var(--color-border)',
            paddingTop: 'env(safe-area-inset-top, 0px)',
            paddingBottom: 'env(safe-area-inset-bottom, 0px)',
          }}
        >
          <div className="flex shrink-0 items-center justify-between border-b px-3 py-3" style={{ borderColor: 'var(--color-border)' }}>
            <Dialog.Title className="text-sm font-semibold" style={{ color: 'var(--color-text-primary)' }}>
              {lang === 'ar' ? 'القائمة' : 'Menu'}
            </Dialog.Title>
            <Dialog.Description className="sr-only">
              {lang === 'ar' ? 'التنقل ومصدر البيانات والشركة' : 'Navigation, data source, and business'}
            </Dialog.Description>
            <Dialog.Close asChild>
              <button
                type="button"
                className="flex h-11 w-11 items-center justify-center rounded-lg border touch-manipulation"
                style={{ borderColor: 'var(--color-border)', color: 'var(--color-text-primary)' }}
                aria-label="Close menu"
              >
                <X className="h-5 w-5" />
              </button>
            </Dialog.Close>
          </div>
          <div className="flex min-h-0 flex-1 flex-col overflow-hidden">
            <SidebarPanel variant="drawer" onInteract={() => setMobileNavOpen(false)} />
          </div>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  )
}
