'use client'
import { useEffect } from 'react'
import { useAppStore, readStoredDataSource, readStoredDensity, applyDensityToDom } from '@/store/useAppStore'

function ExperienceDomSync() {
  const dataSource = useAppStore(s => s.dataSource)
  useEffect(() => {
    document.documentElement.dataset.experience =
      dataSource === 'supermarket' ? 'retail' : 'delivery'
  }, [dataSource])
  return null
}

export function DataProvider({ children }: { children: React.ReactNode }) {
  const fetchData = useAppStore(s => s.fetchData)
  const setDataSource = useAppStore(s => s.setDataSource)

  useEffect(() => {
    const density = readStoredDensity() ?? 'comfortable'
    applyDensityToDom(density)
    useAppStore.setState({ uiDensity: density })

    const saved = readStoredDataSource()
    if (saved) {
      setDataSource(saved)
    } else {
      fetchData()
    }
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <>
      <ExperienceDomSync />
      {children}
    </>
  )
}
