'use client'

export type DecisionWorkflowStatus = 'new' | 'doing' | 'done' | 'dropped'

export interface DecisionWorkflowEntry {
  status: DecisionWorkflowStatus
  assignee: string
  note: string
  updated_at: string
}

const STORAGE_KEY = 'dash_decision_workflow_v1'

function readAll(): Record<string, DecisionWorkflowEntry> {
  if (typeof window === 'undefined') return {}
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return {}
    const p = JSON.parse(raw) as Record<string, DecisionWorkflowEntry>
    return typeof p === 'object' && p !== null ? p : {}
  } catch {
    return {}
  }
}

function writeAll(m: Record<string, DecisionWorkflowEntry>) {
  if (typeof window === 'undefined') return
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(m))
  } catch {
    /* ignore quota */
  }
}

export function getWorkflowEntry(decisionId: string): DecisionWorkflowEntry | undefined {
  return readAll()[decisionId]
}

export function setWorkflowEntry(decisionId: string, patch: Partial<DecisionWorkflowEntry>) {
  const all = readAll()
  const prev = all[decisionId] ?? {
    status: 'new' as const,
    assignee: '',
    note: '',
    updated_at: new Date().toISOString(),
  }
  all[decisionId] = {
    ...prev,
    ...patch,
    updated_at: new Date().toISOString(),
  }
  writeAll(all)
}

export function exportWorkflowJson(): string {
  return JSON.stringify(readAll(), null, 2)
}
