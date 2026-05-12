import { useEffect, useState } from 'react'
import { Surface } from '../../../components/Surface'
import { SectionHeader } from '../components/SectionHeader'
import { DonutChart } from '../components/DonutChart'
import { InfoPanel } from '../components/InfoPanel'
import { api } from '../../../lib/api'
import {
  mockAnalyticsStats,
  mockAnalyticsTrend,
  mockAnalyticsTrendDates,
  mockAnalyticsIntents,
} from '../../../lib/mockData'

const INTENT_COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#8b5cf6', '#ef4444', '#ec4899', '#14b8a6', '#f97316', '#6366f1', '#d1d5db']

export function AnalyticsTab() {
  const [stats, setStats] = useState(mockAnalyticsStats)
  const [trend, setTrend] = useState(mockAnalyticsTrend)
  const [trendDates, setTrendDates] = useState(mockAnalyticsTrendDates)
  const [intents, setIntents] = useState(mockAnalyticsIntents)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function load() {
      try {
        const [apiStats, apiTrend, apiIntents] = await Promise.all([
          api.getAnalyticsStats(),
          api.getAnalyticsTrend(),
          api.getAnalyticsIntents(),
        ])

        setStats([
          { label: 'Total Conversations', value: apiStats.total_conversations.toLocaleString(), delta: '', up: true },
          { label: 'Auto-resolution Rate', value: `${apiStats.auto_resolution_rate}%`, delta: '', up: true },
          { label: 'Hand-off Rate', value: `${apiStats.handoff_rate}%`, delta: '', up: false },
          { label: 'Avg. Response Time', value: apiStats.avg_response_time, delta: '', up: false },
        ])

        if (apiTrend.length > 0) {
          setTrend(apiTrend.map((t) => t.count))
          setTrendDates(apiTrend.map((t) => {
            const d = new Date(t.date)
            return `${d.getDate()} ${d.toLocaleString('en', { month: 'short' })}`
          }))
        }

        if (apiIntents.length > 0) {
          setIntents(apiIntents.map((intent, i) => ({
            label: intent.label,
            pct: intent.pct,
            color: INTENT_COLORS[i % INTENT_COLORS.length],
          })))
        }
      } catch {
        // fallback to mock data (already set)
      } finally {
        setLoading(false)
      }
    }
    void load()
  }, [])

  const trendW = 280
  const trendH = 72
  const maxT = Math.max(...trend, 1)
  const trendPts = trend.map((v, i) => `${(i / Math.max(trend.length - 1, 1)) * trendW},${trendH - (v / maxT) * trendH}`).join(' ')

  return (
    <div className="ai-section ai-tab-shell">
      <SectionHeader
        num="5"
        title="Analytics (System)"
        subtitle="วิเคราะห์การใช้งานระบบ"
        caption="วิเคราะห์การใช้งาน, แนวโน้ม, ปริมาณงาน และประสิทธิภาพของระบบ"
      />
      {loading && <p className="op-empty">Loading analytics...</p>}
      <div className="ai-analytics-layout">
        <div>
          <div className="ai-analytics-stats">
            {stats.map((stat) => (
              <div key={stat.label} className="ai-analytics-stat-card">
                <span className="ai-analytics-stat-label">{stat.label}</span>
                <strong className="ai-analytics-stat-value">{stat.value}</strong>
                {stat.delta && <span className="ai-analytics-delta" style={{ color: stat.up ? '#16a34a' : '#dc2626' }}>{stat.delta}</span>}
              </div>
            ))}
          </div>

          <div className="ai-analytics-charts">
            <Surface title="Conversations Trend">
              <svg viewBox={`0 0 ${trendW} ${trendH + 20}`} className="ai-trend-svg">
                <polyline points={trendPts} fill="none" stroke="#ff6135" strokeWidth="2" strokeLinejoin="round" />
                {trend.map((value, i) => (
                  <circle
                    key={i}
                    cx={(i / Math.max(trend.length - 1, 1)) * trendW}
                    cy={trendH - (value / maxT) * trendH}
                    r="3"
                    fill="#ff6135"
                  />
                ))}
              </svg>
              <div className="ai-trend-dates">
                {trendDates.map((date) => <span key={date}>{date}</span>)}
              </div>
            </Surface>

            <Surface title="Top Intents">
              <div className="ai-intents-chart">
                <DonutChart segments={intents.map((intent) => ({ pct: intent.pct, color: intent.color }))} r={55} />
                <div className="ai-eval-legend">
                  {intents.map((intent) => (
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
