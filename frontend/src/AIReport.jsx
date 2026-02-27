import React, { useState, useEffect } from 'react'
import Markdown from 'react-markdown'

export default function AIReport({ api }) {
    const [report, setReport] = useState(null)
    const [predictions, setPredictions] = useState([])
    const [stats, setStats] = useState(null)
    const [loading, setLoading] = useState(false)
    const [tab, setTab] = useState('sitRep')
    const [generatedAt, setGeneratedAt] = useState(null)

    const loadAll = async () => {
        setLoading(true)
        try {
            const [natRes, predRes] = await Promise.all([
                fetch(`${api}/report/national`).then(r => r.json()),
                fetch(`${api}/predict`).then(r => r.json()),
            ])
            setReport(natRes.report)
            setStats(natRes.stats)
            setGeneratedAt(natRes.generated_at)
            setPredictions(predRes.predictions || [])
        } catch (e) {
            console.error(e)
        } finally {
            setLoading(false)
        }
    }

    useEffect(() => { loadAll() }, [api])

    const PROB_COLOR = {
        High: 'var(--accent-red)',
        Medium: 'var(--accent-amber)',
        Low: 'var(--accent-green)',
    }

    return (
        <div>
            {/* Header */}
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 20 }}>
                <div style={{ display: 'flex', gap: 4 }}>
                    {[
                        { key: 'sitRep', label: '📄 Situation Report' },
                        { key: 'predict', label: '🔮 72hr Predictions' },
                    ].map(t => (
                        <button
                            key={t.key}
                            className="btn"
                            onClick={() => setTab(t.key)}
                            style={{
                                background: tab === t.key ? 'var(--accent-primary)' : 'rgba(255,255,255,0.06)',
                                color: tab === t.key ? 'white' : 'var(--text-secondary)',
                                borderRadius: 8,
                            }}
                        >
                            {t.label}
                        </button>
                    ))}
                </div>

                <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
                    {generatedAt && (
                        <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>
                            Generated {new Date(generatedAt).toLocaleTimeString()}
                        </span>
                    )}
                    <button
                        id="refresh-report-btn"
                        className="btn btn-primary btn-sm"
                        onClick={loadAll}
                        disabled={loading}
                    >
                        {loading ? '⏳ Generating…' : '🤖 Refresh with AI'}
                    </button>
                </div>
            </div>

            {/* Stats bar */}
            {stats && (
                <div style={{ display: 'flex', gap: 12, marginBottom: 24, flexWrap: 'wrap' }}>
                    {[
                        { label: 'Active Disasters', val: stats.active_disasters, color: 'var(--accent-red)' },
                        { label: 'Total Affected', val: (stats.total_affected || 0).toLocaleString(), color: 'var(--accent-amber)' },
                        { label: 'High-Risk Counties', val: stats.high_risk_counties, color: 'var(--risk-high)' },
                        { label: 'Workers Deployed', val: stats.deployed_workers, color: 'var(--accent-primary)' },
                        { label: 'Workers Available', val: stats.available_workers, color: 'var(--accent-green)' },
                    ].map(s => (
                        <div key={s.label} className="card" style={{ padding: '12px 18px', minWidth: 120, flex: 1 }}>
                            <div style={{ fontSize: 22, fontWeight: 800, color: s.color, fontFamily: 'JetBrains Mono, monospace' }}>
                                {s.val}
                            </div>
                            <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 3 }}>{s.label}</div>
                        </div>
                    ))}
                </div>
            )}

            {/* Tab content */}
            {loading ? (
                <div className="loading-center">
                    <div className="spinner" />
                    <span>Gemini is analysing national situation…</span>
                </div>
            ) : tab === 'sitRep' ? (
                <div className="card" style={{ padding: 28 }}>
                    <div className="report-body">
                        {report ? (
                            <Markdown>{report}</Markdown>
                        ) : (
                            <div className="empty-state">
                                <div className="icon">🤖</div>
                                <p>Click "Refresh with AI" to generate a national situation report</p>
                            </div>
                        )}
                    </div>
                </div>
            ) : (
                /* Predictions tab */
                <div>
                    {predictions.length === 0 ? (
                        <div className="card">
                            <div className="empty-state">
                                <div className="icon">🔮</div>
                                <p>No active 72-hour threat predictions</p>
                            </div>
                        </div>
                    ) : (
                        <div className="grid-3">
                            {predictions.map((p, i) => (
                                <div key={i} className="card" style={{ padding: 20 }}>
                                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 10 }}>
                                        <div style={{ fontWeight: 700, fontSize: 15 }}>{p.county}</div>
                                        <span style={{
                                            fontSize: 11, fontWeight: 700,
                                            padding: '3px 9px', borderRadius: 20,
                                            background: `${PROB_COLOR[p.probability]}22`,
                                            color: PROB_COLOR[p.probability],
                                        }}>
                                            {p.probability}
                                        </span>
                                    </div>
                                    <div style={{ fontSize: 22, marginBottom: 6 }}>
                                        {p.threat === 'Flood' ? '🌊' :
                                            p.threat === 'Wildfire' ? '🔥' :
                                                p.threat === 'Drought' ? '☀️' :
                                                    p.threat === 'Landslide' ? '⛰️' : '⚠️'} {p.threat}
                                    </div>
                                    <div style={{ fontSize: 12, color: 'var(--accent-amber)', marginBottom: 8 }}>
                                        ⏰ {p.estimated_time}
                                    </div>
                                    <div style={{
                                        fontSize: 12, color: 'var(--text-secondary)',
                                        background: 'rgba(255,255,255,0.04)',
                                        borderRadius: 6, padding: '8px 10px',
                                        lineHeight: 1.5,
                                    }}>
                                        💡 {p.recommended_action}
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            )}
        </div>
    )
}
