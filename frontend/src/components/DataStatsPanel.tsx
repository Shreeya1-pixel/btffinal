import React from 'react';
import { Database, TrendingUp, AlertTriangle, CheckCircle2, Activity } from 'lucide-react';

interface DataStatsPanelProps {
  stats: any | null;
}

export const DataStatsPanel: React.FC<DataStatsPanelProps> = ({ stats }) => {
  if (!stats) return null;

  const { summary, columns } = stats;
  
  const getQualityColor = (grade: string) => {
    switch (grade) {
      case 'A': return '#10b981';
      case 'B': return '#3b82f6';
      case 'C': return '#f59e0b';
      case 'D': return '#ef4444';
      default: return '#8b92a0';
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      {/* Summary Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 12 }}>
        {/* Data Quality Card */}
        <div className="glass-effect" style={{ 
          padding: 16, 
          border: '1px solid rgba(0, 255, 163, 0.2)', 
          borderRadius: 12,
          background: 'linear-gradient(135deg, rgba(0, 255, 163, 0.05) 0%, rgba(15, 23, 42, 0.4) 100%)'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
            <CheckCircle2 size={18} color={getQualityColor(summary.quality_grade)} />
            <div style={{ fontSize: 11, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
              Data Quality
            </div>
          </div>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: 6 }}>
            <span style={{ fontSize: 32, fontWeight: 700, color: getQualityColor(summary.quality_grade) }}>
              {summary.quality_grade}
            </span>
            <span style={{ fontSize: 14, color: 'var(--text-secondary)' }}>
              {summary.quality_score}%
            </span>
          </div>
        </div>

        {/* Dataset Size Card */}
        <div className="glass-effect" style={{ 
          padding: 16, 
          border: '1px solid rgba(0, 229, 255, 0.2)', 
          borderRadius: 12,
          background: 'linear-gradient(135deg, rgba(0, 229, 255, 0.05) 0%, rgba(15, 23, 42, 0.4) 100%)'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
            <Database size={18} color="var(--accent-secondary)" />
            <div style={{ fontSize: 11, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
              Dataset Size
            </div>
          </div>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: 6 }}>
            <span style={{ fontSize: 28, fontWeight: 700, color: 'var(--text-primary)' }}>
              {summary.total_rows.toLocaleString()}
            </span>
            <span style={{ fontSize: 14, color: 'var(--text-secondary)' }}>
              rows × {summary.total_columns} cols
            </span>
          </div>
        </div>

        {/* Fill Rate Card */}
        <div className="glass-effect" style={{ 
          padding: 16, 
          border: '1px solid rgba(168, 178, 200, 0.2)', 
          borderRadius: 12,
          background: 'linear-gradient(135deg, rgba(168, 178, 200, 0.05) 0%, rgba(15, 23, 42, 0.4) 100%)'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
            <Activity size={18} color="var(--text-secondary)" />
            <div style={{ fontSize: 11, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
              Avg Fill Rate
            </div>
          </div>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: 6 }}>
            <span style={{ fontSize: 28, fontWeight: 700, color: 'var(--text-primary)' }}>
              {summary.avg_fill_rate}%
            </span>
            <span style={{ fontSize: 14, color: 'var(--text-secondary)' }}>
              completeness
            </span>
          </div>
        </div>

        {/* Memory Card */}
        <div className="glass-effect" style={{ 
          padding: 16, 
          border: '1px solid rgba(255, 166, 0, 0.2)', 
          borderRadius: 12,
          background: 'linear-gradient(135deg, rgba(255, 166, 0, 0.05) 0%, rgba(15, 23, 42, 0.4) 100%)'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
            <TrendingUp size={18} color="#ffa600" />
            <div style={{ fontSize: 11, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
              Memory
            </div>
          </div>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: 6 }}>
            <span style={{ fontSize: 28, fontWeight: 700, color: 'var(--text-primary)' }}>
              {summary.memory_kb < 1024 ? summary.memory_kb.toFixed(1) : (summary.memory_kb / 1024).toFixed(2)}
            </span>
            <span style={{ fontSize: 14, color: 'var(--text-secondary)' }}>
              {summary.memory_kb < 1024 ? 'KB' : 'MB'}
            </span>
          </div>
        </div>
      </div>

      {/* Column Details */}
      <div className="glass-effect" style={{ 
        padding: 16, 
        border: '1px solid var(--border-primary)', 
        borderRadius: 12,
        background: 'rgba(15, 23, 42, 0.4)',
        maxHeight: 400,
        overflowY: 'auto'
      }}>
        <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-secondary)', marginBottom: 12, textTransform: 'uppercase', letterSpacing: '0.5px' }}>
          Column Analysis ({columns.length})
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          {columns.map((col: any, idx: number) => (
            <div key={idx} style={{ 
              padding: 12, 
              background: 'rgba(30, 41, 59, 0.4)', 
              border: '1px solid rgba(255, 255, 255, 0.05)', 
              borderRadius: 8,
              transition: 'all 0.2s ease'
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 8 }}>
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-primary)', fontFamily: 'var(--font-mono)' }}>
                    {col.name}
                  </div>
                  <div style={{ fontSize: 11, color: 'var(--text-tertiary)', marginTop: 2 }}>
                    {col.dtype} • {col.unique_values} unique • {col.cardinality} cardinality
                  </div>
                </div>
                <div style={{ 
                  padding: '4px 8px', 
                  background: col.fill_rate >= 95 ? 'rgba(0, 255, 163, 0.1)' : col.fill_rate >= 70 ? 'rgba(255, 166, 0, 0.1)' : 'rgba(255, 71, 87, 0.1)',
                  border: `1px solid ${col.fill_rate >= 95 ? 'rgba(0, 255, 163, 0.3)' : col.fill_rate >= 70 ? 'rgba(255, 166, 0, 0.3)' : 'rgba(255, 71, 87, 0.3)'}`,
                  borderRadius: 6,
                  fontSize: 11,
                  fontWeight: 600,
                  color: col.fill_rate >= 95 ? '#00ffa3' : col.fill_rate >= 70 ? '#ffa600' : '#ff4757'
                }}>
                  {col.fill_rate}%
                </div>
              </div>
              
              {/* Numeric Stats */}
              {col.mean !== undefined && (
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(80px, 1fr))', gap: 8, marginTop: 8, paddingTop: 8, borderTop: '1px solid rgba(255, 255, 255, 0.05)' }}>
                  <div>
                    <div style={{ fontSize: 9, color: 'var(--text-tertiary)', textTransform: 'uppercase' }}>Mean</div>
                    <div style={{ fontSize: 12, color: 'var(--text-primary)', fontWeight: 600 }}>{col.mean}</div>
                  </div>
                  <div>
                    <div style={{ fontSize: 9, color: 'var(--text-tertiary)', textTransform: 'uppercase' }}>Median</div>
                    <div style={{ fontSize: 12, color: 'var(--text-primary)', fontWeight: 600 }}>{col.median}</div>
                  </div>
                  <div>
                    <div style={{ fontSize: 9, color: 'var(--text-tertiary)', textTransform: 'uppercase' }}>Std</div>
                    <div style={{ fontSize: 12, color: 'var(--text-primary)', fontWeight: 600 }}>{col.std}</div>
                  </div>
                  <div>
                    <div style={{ fontSize: 9, color: 'var(--text-tertiary)', textTransform: 'uppercase' }}>Range</div>
                    <div style={{ fontSize: 12, color: 'var(--text-primary)', fontWeight: 600 }}>{col.min}–{col.max}</div>
                  </div>
                  {col.outliers_count !== undefined && (
                    <div>
                      <div style={{ fontSize: 9, color: 'var(--text-tertiary)', textTransform: 'uppercase' }}>Outliers</div>
                      <div style={{ fontSize: 12, color: col.outliers_pct > 5 ? '#ff4757' : 'var(--text-primary)', fontWeight: 600 }}>
                        {col.outliers_count} ({col.outliers_pct}%)
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* Missing Values Warning */}
              {col.missing_count > 0 && (
                <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginTop: 8, padding: 8, background: 'rgba(255, 166, 0, 0.1)', border: '1px solid rgba(255, 166, 0, 0.2)', borderRadius: 6 }}>
                  <AlertTriangle size={14} color="#ffa600" />
                  <span style={{ fontSize: 11, color: '#ffa600' }}>
                    {col.missing_count} missing values ({(100 - col.fill_rate).toFixed(1)}%)
                  </span>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

