import { useEffect, useState } from 'react'
import { Surface } from '../../../components/Surface'
import { SectionHeader } from '../components/SectionHeader'
import { DonutChart } from '../components/DonutChart'
import { InfoPanel } from '../components/InfoPanel'
import { api } from '../../../lib/api'
import { mockEvalStats, mockEvalSegments, mockEvalLegend } from '../../../lib/mockData'

export function EvaluationTab() {
  const [evalStats, setEvalStats] = useState(mockEvalStats)
  const [segments, setSegments] = useState(mockEvalSegments)
  const [legend, setLegend] = useState(mockEvalLegend)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function load() {
      try {
        const data = await api.getEvalSummary()

        setEvalStats([
          { label: 'Total Traces', value: String(data.total_traces) },
          { label: 'Success', value: String(data.success) },
          { label: 'Pass Rate (Overall)', value: `${data.success_pct}%`, green: true },
          { label: 'Last Run', value: data.last_run ? new Date(data.last_run).toLocaleDateString('th-TH') : 'N/A' },
        ])

        setSegments([
          { pct: data.success_pct, color: '#10b981' },
          { pct: data.failed_pct, color: '#ef4444' },
          { pct: data.partial_pct, color: '#f59e0b' },
        ])

        setLegend([
          { label: 'Success', value: `${data.success} (${data.success_pct}%)`, color: '#10b981' },
          { label: 'Failed', value: `${data.failed} (${data.failed_pct}%)`, color: '#ef4444' },
          { label: 'Other', value: `${data.partial} (${data.partial_pct}%)`, color: '#f59e0b' },
        ])
      } catch {
        // fallback to mock data
      } finally {
        setLoading(false)
      }
    }
    void load()
  }, [])

  return (
    <div className="ai-section ai-tab-shell">
      <SectionHeader
        num="4"
        title="Evaluation"
        subtitle="ประเมินประสิทธิภาพ AI"
        caption="สร้างชุดทดสอบ, รันการประเมิน และวัดผลความถูกต้องของระบบ"
      />
      {loading && <p className="op-empty">Loading evaluation data...</p>}
      <div className="ai-eval-layout">
        <div>
          <div className="ai-eval-stats">
            {evalStats.map((stat) => (
              <div key={stat.label} className="ai-eval-stat-card">
                <span className="ai-eval-stat-label">{stat.label}</span>
                <strong className="ai-eval-stat-value" style={{ color: stat.green ? '#16a34a' : undefined }}>{stat.value}</strong>
              </div>
            ))}
          </div>

          <Surface title="Latest Evaluation Result">
            <div className="ai-eval-chart">
              <DonutChart segments={segments} r={65} />
              <div className="ai-eval-legend">
                {legend.map((item) => (
                  <div key={item.label} className="ai-eval-legend-item">
                    <span className="ai-eval-legend-dot" style={{ background: item.color }} />
                    <span>{item.label}</span>
                    <strong>{item.value}</strong>
                  </div>
                ))}
              </div>
            </div>
          </Surface>
        </div>
        <InfoPanel
          main={['สร้าง Test Case', 'กำหนด Expected', 'ทำ Evaluation', 'วิเคราะห์ผลลัพธ์', 'ดูแนวโน้ม']}
          features={['Test Case Manager', 'Auto Evaluation', 'Metrics & Score', 'Report & Export', 'Access Control']}
        />
      </div>
    </div>
  )
}
