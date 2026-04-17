'use client'
import { useEffect } from 'react'
import { useAppStore, readStoredDataSource } from '@/store/useAppStore'

export function DataProvider({ children }: { children: React.ReactNode }) {
  const fetchData = useAppStore(s => s.fetchData)
  const setDataSource = useAppStore(s => s.setDataSource)

  useEffect(() => {
    const saved = readStoredDataSource()
    if (saved) {
      setDataSource(saved)
    } else {
      fetchData()
    }
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  return <>{children}</>
}
