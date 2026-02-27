import React, { useState, useEffect } from 'react'

const RISK_CLASS = (score) => {
    if (score >= 80) return 'risk-critical'
    if (score >= 60) return 'risk-high'
    if (score >= 40) return 'risk-medium'
    if (score >= 20) return 'risk-low'
    return 'risk-none'
}

const RISK_LABEL = (score) => {
    if (score >= 80) return { label: 'Critical', color: 'var(--risk-critical)' }
    if (score >= 60) return { label: 'High', color: 'var(--risk-high)' }
    if (score >= 40) return { label: 'Medium', color: 'var(--risk-medium)' }
    if (score >= 20) return { label: 'Low', color: 'var(--risk-low)' }
    return { label: 'Safe', color: 'var(--risk-none)' }
}

export default function RiskPanel({ api }) {
    const [counties, setCounties] = useState([])
    const [loading, setLoading] = useState(true)
    const [sort, setSort] = useState('risk')
    const [filter, setFilter] = useState('')

    useEffect(() => {
        fetch(`${api}/counties/risk`)
            .then(r => r.json())
            .then(data => { setCounties(data); setLoading(false) })
            .catch(() => setLoading(false))
    }, [api])

    const filtered = counties
        .filter(c => c.name.toLowerCase().includes(filter.toLowerCase()))
        .sort((a, b) => sort === 'risk'
            ? (b.risk_score || 0) - (a.risk_score || 0)
            : a.name.localeCompare(b.name)
        )

    const highCount = counties.filter(c => (c.risk_score || 0) >= 70).length
    const mediumCount = counties.filter(c => (c.risk_score || 0) >= 40 && c.risk_score < 70).length

    if (loading) return (
        <div className="loading-center"><div className="spinner" /><span>Loading county data…</span></div>
    )

    return (
        <div>
            {/* Summary bar */}
            <div style={{ display: 'flex', gap: 12, marginBottom: 20, flexWrap: 'wrap' }}>
                {[
                    { label: 'High Risk', count: highCount, color: 'var(--risk-high)' },
                    { label: 'Medium Risk', count: mediumCount, color: 'var(--risk-medium)' },
                    { label: 'Monitored', count: counties.length, color: 'var(--accent-primary)' },
                ].map(s => (
                    <div key={s.label} className="card" style={{ padding: '12px 20px', display: 'flex', alignItems: 'center', gap: 12 }}>
                        <span style={{ fontSize: 22, fontWeight: 800, color: s.color }}>{s.count}</span>
                        <span style={{ fontSize: 13, color: 'var(--text-secondary)' }}>{s.label}</span>
                    </div>
                ))}

                <div style={{ marginLeft: 'auto', display: 'flex', gap: 10, alignItems: 'center' }}>
                    <input
                        className="form-control"
                        placeholder="🔍 Search county…"
                        value={filter}
                        onChange={e => setFilter(e.target.value)}
                        style={{ width: 180, padding: '8px 12px' }}
                    />
                    <select
                        className="form-control"
                        value={sort}
                        onChange={e => setSort(e.target.value)}
                        style={{ width: 140, padding: '8px 12px' }}
                    >
                        <option value="risk">Sort: Risk ↓</option>
                        <option value="name">Sort: Name A–Z</option>
                    </select>
                </div>
            </div>

            {/* County grid */}
            <div className="grid-3">
                {filtered.map(county => {
                    const score = county.risk_score || 0
                    const rl = RISK_LABEL(score)
                    const pct = Math.min(score, 100)
                    return (
                        <div key={county.id} className="card" style={{ padding: '16px 18px', cursor: 'default' }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 10 }}>
                                <div>
                                    <div style={{ fontWeight: 700, fontSize: 14 }}>{county.name}</div>
                                    <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 2 }}>{county.region}</div>
                                </div>
                                <div style={{
                                    fontSize: 22, fontWeight: 800, fontFamily: 'JetBrains Mono, monospace',
                                    color: rl.color,
                                }}>
                                    {score}
                                </div>
                            </div>

                            {/* Risk bar */}
                            <div style={{
                                height: 5, borderRadius: 3,
                                background: 'rgba(255,255,255,0.08)',
                                marginBottom: 8,
                                overflow: 'hidden',
                            }}>
                                <div style={{
                                    height: '100%',
                                    width: `${pct}%`,
                                    background: rl.color,
                                    borderRadius: 3,
                                    transition: 'width 0.6s ease',
                                    boxShadow: `0 0 6px ${rl.color}`,
                                }} />
                            </div>

                            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11 }}>
                                <span style={{ color: rl.color, fontWeight: 600 }}>{rl.label}</span>
                                {county.last_updated && (
                                    <span style={{ color: 'var(--text-muted)' }}>
                                        {new Date(county.last_updated).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                                    </span>
                                )}
                            </div>
                        </div>
                    )
                })}
            </div>
        </div>
    )
}
