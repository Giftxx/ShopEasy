import type { ReactNode } from 'react'
import { useSearchParams } from 'react-router-dom'

import { Sidebar } from '../../components/Sidebar'
import { readSession } from '../../lib/session'

import { SvgIcon } from './components/SvgIcon'
import { WorkspaceTab } from './tabs/WorkspaceTab'
import { TracesTab } from './tabs/TracesTab'
import { EvaluationTab } from './tabs/EvaluationTab'
import { AnalyticsTab } from './tabs/AnalyticsTab'

type AiTab = 'workspace' | 'traces' | 'evaluation' | 'analytics'

const navItems: { key: AiTab; label: string; icon: ReactNode }[] = [
  {
    key: 'workspace',
    label: 'Multi-Agent Workspace',
    icon: (
      <SvgIcon
        path={
          <>
            <rect x="4" y="6" width="16" height="10" rx="2" fill="none" stroke="currentColor" strokeWidth="1.6" />
            <path d="M4 11h16M8 16v3M16 16v3" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
            <circle cx="8" cy="13.5" r="1.5" fill="currentColor" />
            <circle cx="16" cy="13.5" r="1.5" fill="currentColor" />
          </>
        }
      />
    ),
  },
  {
    key: 'traces',
    label: 'Agent Traces',
    icon: (
      <SvgIcon
        path={
          <>
            <circle cx="11" cy="11" r="5.6" fill="none" stroke="currentColor" strokeWidth="1.7" />
            <path d="m15.2 15.2 4.1 4.1" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" />
          </>
        }
      />
    ),
  },
  {
    key: 'evaluation',
    label: 'Evaluation',
    icon: (
      <SvgIcon
        path={
          <>
            <path d="M6 19V8m6 11V5m6 14v-8" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
            <path d="M4 19h16" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
          </>
        }
      />
    ),
  },
  {
    key: 'analytics',
    label: 'Analytics (System)',
    icon: (
      <SvgIcon
        path={
          <>
            <path d="M5 18 10 13l3 3 6-7" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
            <path d="M5 6v12h14" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
          </>
        }
      />
    ),
  },
]

export function AiControlPortal() {
  const [searchParams, setSearchParams] = useSearchParams()
  const activeTab = (searchParams.get('tab') as AiTab) ?? 'workspace'
  const setActiveTab = (tab: AiTab) => setSearchParams({ tab }, { replace: true })
  const session = readSession()
  const userName = session?.user?.name ?? 'AI Admin'

  return (
    <div className="ai-control-page">
      <Sidebar
        title="ShopEasy"
        subtitle="AI Control"
        accent="linear-gradient(135deg, #ff5d2e, #ff8744)"
        items={navItems}
        activeKey={activeTab}
        onSelect={(key) => setActiveTab(key as AiTab)}
        className="sidebar--ai-control"
        footer={
          <div className="sidebar-profile">
            <strong>{userName}</strong>
            <span>{session?.user?.email ?? 'ai_admin'}</span>
          </div>
        }
      />

      <div className="ai-portal-main">
        <div className="ai-portal-topbar">
          <span className="ai-portal-topbar__title">
            {navItems.find((n) => n.key === activeTab)?.label}
          </span>
        </div>
        <div className="ai-portal-content">
          {activeTab === 'workspace' && <WorkspaceTab />}
          {activeTab === 'traces' && <TracesTab />}
          {activeTab === 'evaluation' && <EvaluationTab />}
          {activeTab === 'analytics' && <AnalyticsTab />}
        </div>
      </div>
    </div>
  )
}
