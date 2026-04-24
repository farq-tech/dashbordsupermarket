'use client'
import { useEffect } from 'react'
import { readStoredPersona } from '@/lib/businessPersona'
import { useAppStore, readStoredDataSource, readStoredDensity, applyDensityToDom } from '@/store/useAppStore'

export function DataProvider({ children }: { children: React.ReactNode }) {
  const fetchData = useAppStore(s => s.fetchData)
  const setDataSource = useAppStore(s => s.setDataSource)

  useEffect(() => {
    const density = readStoredDensity() ?? 'comfortable'
    applyDensityToDom(density)
    useAppStore.setState({ uiDensity: density })

    const savedPersona = readStoredPersona()
    if (savedPersona) {
      useAppStore.setState({ businessPersona: savedPersona })
    }

    const saved = readStoredDataSource()
    if (saved) {
      setDataSource(saved)
    } else {
      fetchData()
    }
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  return <>{children}</>
}
