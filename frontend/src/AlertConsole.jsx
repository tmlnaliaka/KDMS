import React, { useState, useEffect } from 'react'

export default function AlertConsole({ api }) {
    const [disasters, setDisasters] = useState([])
    const [disId, setDisId] = useState('')
    const [preview, setPreview] = useState(null)
    const [pastAlerts, setPastAlerts] = useState([])
    const [loading, setLoading] = useState(false)
    const [generating, setGenerating] = useState(false)
    const [toast, setToast] = useState(null)
    const [sending, setSending] = useState(false)

    useEffect(() => {
        fetch(`${api}/disasters?status=active`).then(r => r.json()).then(setDisasters).catch(() => { })
        fetch(`${api}/alerts`).then(r => r.json()).then(setPastAlerts).catch(() => { })
    }, [api])

    const showToast = (msg, type = 'success') => {
        setToast({ msg, type })
        setTimeout(() => setToast(null), 4000)
    }

    const generatePreview = async () => {
        if (!disId) return
        setGenerating(true)
        setPreview(null)
        try {
            // Use /alert/send endpoint but we read the response without triggering full send
            // Better: we call the endpoint which returns the preview without actually sending yet
            const res = await fetch(`${api}/alert/send`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ disaster_id: parseInt(disId) }),
            })
            const data = await res.json()
            setPreview(data)
            // Refresh past alerts list
            fetch(`${api}/alerts`).then(r => r.json()).then(setPastAlerts).catch(() => { })
            showToast(`✅ Alert sent to ${data.recipients} recipient${data.recipients !== 1 ? 's' : ''}`)
        } catch {
            showToast('❌ Failed to send alert', 'error')
        } finally {
            setGenerating(false)
        }
    }

    const selectedDisaster = disasters.find(d => d.id === parseInt(disId))

    return (
        <div>
            <div className="grid-2" style={{ gap: 20 }}>
                {/* Left: composer */}
                <div className="card" style={{ padding: 24 }}>
                    <div style={{ fontWeight: 700, fontSize: 16, marginBottom: 20 }}>📱 Compose Alert</div>

                    <div className="form-group">
                        <label>Select Disaster</label>
                        <select
                            id="alert-disaster-select"
                            className="form-control"
                            value={disId}
                            onChange={e => { setDisId(e.target.value); setPreview(null) }}
                        >
                            <option value="">— Choose active disaster —</option>
                            {disasters.map(d => (
                                <option key={d.id} value={d.id}>
                                    {d.type} — {d.location} ({d.severity})
                                </option>
                            ))}
                        </select>
                    </div>

                    {selectedDisaster && (
                        <div style={{
                            background: 'rgba(255,255,255,0.04)',
                            border: '1px solid var(--glass-border)',
                            borderRadius: 8, padding: 12, marginBottom: 16,
                        }}>
                            <div style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 6 }}>DISASTER DETAILS</div>
                            <div style={{ fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.6 }}>
                                <div>📍 <b>{selectedDisaster.location}</b></div>
                                <div>⚡ Severity: <span style={{
                                    color: selectedDisaster.severity === 'High' ? 'var(--accent-red)' :
                                        selectedDisaster.severity === 'Medium' ? 'var(--accent-amber)' : 'var(--accent-green)'
                                }}>{selectedDisaster.severity}</span></div>
                                <div>👥 Affected: {(selectedDisaster.affected_people || 0).toLocaleString()}</div>
                            </div>
                        </div>
                    )}

                    <button
                        id="send-alert-btn"
                        className="btn btn-primary"
                        style={{ width: '100%', justifyContent: 'center', padding: '11px' }}
                        disabled={!disId || generating}
                        onClick={generatePreview}
                    >
                        {generating ? '⏳ Generating AI alert…' : '🤖 Generate & Send AI Alert'}
                    </button>

                    <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 10, textAlign: 'center' }}>
                        Gemini generates English + Swahili SMS · Sent via Africa's Talking
                    </div>
                </div>

                {/* Right: preview */}
                <div className="card" style={{ padding: 24 }}>
                    <div style={{ fontWeight: 700, fontSize: 16, marginBottom: 16 }}>📋 Alert Preview</div>

                    {!preview ? (
                        <div className="empty-state">
                            <div className="icon">📨</div>
                            <p>Select a disaster and click "Generate" to preview the AI-crafted alert</p>
                        </div>
                    ) : (
                        <div>
                            <div style={{ marginBottom: 16 }}>
                                <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--accent-primary)', marginBottom: 6, textTransform: 'uppercase', letterSpacing: '.5px' }}>
                                    🇬🇧 English
                                </div>
                                <div className="sms-preview">{preview.message_en}</div>
                                <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 4 }}>
                                    {(preview.message_en || '').length} / 160 chars
                                </div>
                            </div>

                            <div style={{ marginBottom: 16 }}>
                                <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--accent-cyan)', marginBottom: 6, textTransform: 'uppercase', letterSpacing: '.5px' }}>
                                    🇰🇪 Swahili
                                </div>
                                <div className="sms-preview">{preview.message_sw}</div>
                                <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 4 }}>
                                    {(preview.message_sw || '').length} / 160 chars
                                </div>
                            </div>

                            <div style={{
                                display: 'flex', alignItems: 'center', gap: 8,
                                padding: '10px 14px',
                                background: 'rgba(16,185,129,0.1)',
                                border: '1px solid rgba(16,185,129,0.25)',
                                borderRadius: 8, fontSize: 13,
                            }}>
                                <span>✅</span>
                                <span style={{ color: 'var(--accent-green)' }}>
                                    Sent to <b>{preview.recipients}</b> recipient{preview.recipients !== 1 ? 's' : ''}
                                </span>
                            </div>
                        </div>
                    )}
                </div>
            </div>

            {/* Past alerts */}
            <div className="card" style={{ marginTop: 24 }}>
                <div className="card-header">
                    <h2>📜 Alert History</h2>
                    <button
                        className="btn btn-sm"
                        style={{ background: 'rgba(255,255,255,0.06)', color: 'var(--text-secondary)' }}
                        onClick={() => fetch(`${api}/alerts`).then(r => r.json()).then(setPastAlerts).catch(() => { })}
                    >
                        🔄 Refresh
                    </button>
                </div>
                <div style={{ overflowX: 'auto' }}>
                    <table className="data-table">
                        <thead>
                            <tr>
                                <th>Sent At</th>
                                <th>Disaster #</th>
                                <th>English Message</th>
                                <th>Recipients</th>
                                <th>Status</th>
                            </tr>
                        </thead>
                        <tbody>
                            {pastAlerts.length === 0 ? (
                                <tr>
                                    <td colSpan={5} style={{ textAlign: 'center', color: 'var(--text-muted)', padding: 28 }}>
                                        No alerts sent yet
                                    </td>
                                </tr>
                            ) : pastAlerts.map(a => (
                                <tr key={a.id}>
                                    <td style={{ fontSize: 12, color: 'var(--text-muted)', whiteSpace: 'nowrap' }}>
                                        {new Date(a.sent_at).toLocaleString()}
                                    </td>
                                    <td>#{a.disaster_id}</td>
                                    <td style={{ maxWidth: 300, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', fontSize: 12, color: 'var(--text-secondary)' }}>
                                        {a.message_en}
                                    </td>
                                    <td style={{ textAlign: 'center' }}>{a.recipients_count}</td>
                                    <td><span className="badge badge-active">{a.status}</span></td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>

            {toast && <div className={`toast ${toast.type}`}>{toast.msg}</div>}
        </div>
    )
}
