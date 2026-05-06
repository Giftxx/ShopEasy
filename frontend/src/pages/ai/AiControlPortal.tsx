import type { ReactNode } from 'react'
import { useState } from 'react'

import { PortalShell } from '../../components/PortalShell'
import { Sidebar } from '../../components/Sidebar'

import { SvgIcon } from './components/SvgIcon'
import { WorkspaceTab } from './tabs/WorkspaceTab'
import { TracesTab } from './tabs/TracesTab'
import { RagTab } from './tabs/RagTab'
import { EvaluationTab } from './tabs/EvaluationTab'
import { AnalyticsTab } from './tabs/AnalyticsTab'

type AiTab = 'workspace' | 'traces' | 'rag' | 'evaluation' | 'analytics'

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
    key: 'rag',
    label: 'Policies / RAG',
    icon: (
      <SvgIcon
        path={
          <>
            <rect x="6" y="4" width="12" height="16" rx="1.8" fill="none" stroke="currentColor" strokeWidth="1.6" />
            <path d="M9 8h6M9 12h6M9 16h4" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
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
  const [activeTab, setActiveTab] = useState<AiTab>('workspace')

  return (
    <PortalShell
      badge="AI Control"
      heading="AI Engineer / System Admin"
      caption="ศูนย์ควบคุม traces, logs และความเชื่อมโยงกับเคสจริงในระบบ"
      variant="ai-control"
    >
      <div className="ai-control-page">
        <Sidebar
          items={navItems}
          activeKey={activeTab}
          onChange={(key) => setActiveTab(key as AiTab)}
          variant="ai"
        />

        <div className="portal-main portal-main--ai-control">
          <div className="ai-control-header">
            <h2>{navItems.find((n) => n.key === activeTab)?.label}</h2>
            <p>ศูนย์ควบคุม traces, logs และความเชื่อมโยงกับเคสจริงในระบบ</p>
          </div>

          {activeTab === 'workspace' && <WorkspaceTab />}
          {activeTab === 'traces' && <TracesTab />}
          {activeTab === 'rag' && <RagTab />}
          {activeTab === 'evaluation' && <EvaluationTab />}
          {activeTab === 'analytics' && <AnalyticsTab />}

          <div className="ai-control-footer">
            <span>© 2024 AI Control. All rights reserved.</span>
            <div className="ai-control-footer__links">
              <button type="button">Privacy Policy</button>
              <button type="button">Terms of Service</button>
            </div>
          </div>
        </div>
      </div>
    </PortalShell>
  )
}
