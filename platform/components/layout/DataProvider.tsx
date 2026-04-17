'use client'
import { useEffect } from 'react'
import { useAppStore } from '@/store/useAppStore'

export function DataProvider({ children }: { children: React.ReactNode }) {
  const { fetchData, selectedRetailer, dashboardData } = useAppStore()

  useEffect(() => {
    if (!dashboardData) {
      fetchData(selectedRetailer?.store_key)
    }
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  return <>{children}</>
}
