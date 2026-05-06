import { Surface } from '../../../components/Surface'
import { SectionHeader } from '../components/SectionHeader'
import { DonutChart } from '../components/DonutChart'
import { InfoPanel } from '../components/InfoPanel'

export function EvaluationTab() {
  return (
    <div className="ai-section ai-tab-shell">
      <SectionHeader
        num="4"
        title="Evaluation"
        subtitle="ประเมินประสิทธิภาพ AI"
        caption="สร้างชุดทดสอบ, รันการประเมิน และวัดผลความถูกต้องของระบบ"
      />
      <div className="ai-eval-layout">
        <div>
          <div className="ai-eval-stats">
            {[
              { label: 'Total Test Sets', value: '24' },
              { label: 'Total Cases', value: '512' },
              { label: 'Pass Rate (Overall)', value: '92.1%', green: true },
              { label: 'Last Run', value: '16/05/2024' },
            ].map((stat) => (
              <div key={stat.label} className="ai-eval-stat-card">
                <span className="ai-eval-stat-label">{stat.label}</span>
                <strong className="ai-eval-stat-value" style={{ color: stat.green ? '#16a34a' : undefined }}>{stat.value}</strong>
              </div>
            ))}
          </div>

          <Surface title="Latest Evaluation Result">
            <div className="ai-eval-chart">
              <DonutChart segments={[{ pct: 92.1, color: '#10b981' }, { pct: 6.6, color: '#ef4444' }, { pct: 1.3, color: '#f59e0b' }]} r={65} />
              <div className="ai-eval-legend">
                {[
                  { label: 'Pass', value: '472 (92.1%)', color: '#10b981' },
                  { label: 'Fail', value: '34 (6.6%)', color: '#ef4444' },
                  { label: 'Partial', value: '6 (1.3%)', color: '#f59e0b' },
                ].map((item) => (
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
