import { Surface } from '../../../components/Surface'
import { SectionHeader } from '../components/SectionHeader'
import { DonutChart } from '../components/DonutChart'
import { InfoPanel } from '../components/InfoPanel'

const TREND = [25, 45, 30, 55, 40, 60, 45, 70, 50, 65, 55, 75]
const TREND_DATES = ['12 May', '13 May', '14 May', '15 May', '16 May']

const INTENTS = [
  { label: 'order_status', pct: 30, color: '#3b82f6' },
  { label: 'refund_request', pct: 28, color: '#10b981' },
  { label: 'delivery_delay', pct: 18, color: '#f59e0b' },
  { label: 'return_request', pct: 10, color: '#8b5cf6' },
  { label: 'other', pct: 9, color: '#d1d5db' },
]

export function AnalyticsTab() {
  const trendW = 280
  const trendH = 72
  const maxT = Math.max(...TREND)
  const trendPts = TREND.map((v, i) => `${(i / (TREND.length - 1)) * trendW},${trendH - (v / maxT) * trendH}`).join(' ')

  return (
    <div className="ai-section ai-tab-shell">
      <SectionHeader
        num="5"
        title="Analytics (System)"
        subtitle="วิเคราะห์การใช้งานระบบ"
        caption="วิเคราะห์การใช้งาน, แนวโน้ม, ปริมาณงาน และประสิทธิภาพของระบบ"
      />
      <div className="ai-analytics-layout">
        <div>
          <div className="ai-analytics-stats">
            {[
              { label: 'Total Conversations', value: '128,542', delta: '+12.3%', up: true },
              { label: 'Auto-resolution Rate', value: '67.7%', delta: '+4.3%', up: true },
              { label: 'Hand-off Rate', value: '32.3%', delta: '-4.3%', up: false },
              { label: 'Avg. Response Time', value: '1.8s', delta: '-0.2s', up: false },
            ].map((stat) => (
              <div key={stat.label} className="ai-analytics-stat-card">
                <span className="ai-analytics-stat-label">{stat.label}</span>
                <strong className="ai-analytics-stat-value">{stat.value}</strong>
                <span className="ai-analytics-delta" style={{ color: stat.up ? '#16a34a' : '#dc2626' }}>{stat.delta}</span>
              </div>
            ))}
          </div>

          <div className="ai-analytics-charts">
            <Surface title="Conversations Trend">
              <svg viewBox={`0 0 ${trendW} ${trendH + 20}`} className="ai-trend-svg">
                <polyline points={trendPts} fill="none" stroke="#3b82f6" strokeWidth="2" strokeLinejoin="round" />
                {TREND.map((value, i) => (
                  <circle
                    key={i}
                    cx={(i / (TREND.length - 1)) * trendW}
                    cy={trendH - (value / maxT) * trendH}
                    r="3"
                    fill="#3b82f6"
                  />
                ))}
              </svg>
              <div className="ai-trend-dates">
                {TREND_DATES.map((date) => <span key={date}>{date}</span>)}
              </div>
            </Surface>

            <Surface title="Top Intents">
              <div className="ai-intents-chart">
                <DonutChart segments={INTENTS.map((intent) => ({ pct: intent.pct, color: intent.color }))} r={55} />
                <div className="ai-eval-legend">
                  {INTENTS.map((intent) => (
                    <div key={intent.label} className="ai-eval-legend-item">
                      <span className="ai-eval-legend-dot" style={{ background: intent.color }} />
                      <span>{intent.label}</span>
                      <strong>{intent.pct}%</strong>
                    </div>
                  ))}
                </div>
              </div>
            </Surface>
          </div>
        </div>
        <InfoPanel
          main={['ดู Metrics หลัก', 'ดูแนวโน้มการใช้งาน', 'ดู Top Intents', 'วิเคราะห์ปัญหา', 'ส่งออก Report']}
          features={['Real-time Dashboard', 'Custom Reports', 'Drill-down', 'Export (CSV/PDF)']}
        />
      </div>
    </div>
  )
}
