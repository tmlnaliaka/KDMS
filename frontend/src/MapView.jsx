import React, { useState, useEffect, useRef } from 'react'
import { MapContainer, TileLayer, CircleMarker, Popup, useMap, GeoJSON } from 'react-leaflet'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'

const SEVERITY_COLOR = {
    High: '#ef4444',
    Medium: '#f59e0b',
    Low: '#10b981',
}

const TYPE_ICON = {
    Flood: '🌊',
    Wildfire: '🔥',
    Drought: '☀️',
    Earthquake: '🌎',
    Landslide: '⛰️',
    default: '⚠️',
}

function FitBounds({ disasters }) {
    const map = useMap()
    useEffect(() => {
        if (disasters.length) {
            const lats = disasters.map(d => d.lat).filter(Boolean)
            const lngs = disasters.map(d => d.lng).filter(Boolean)
            if (lats.length && lngs.length) {
                map.fitBounds(
                    [[Math.min(...lats) - 0.5, Math.min(...lngs) - 0.5],
                    [Math.max(...lats) + 0.5, Math.max(...lngs) + 0.5]],
                    { maxZoom: 9 }
                )
            }
        }
    }, [disasters])
    return null
}

export default function MapView({ api }) {
    const [disasters, setDisasters] = useState([])
    const [countyRisks, setCountyRisks] = useState([])
    const [selected, setSelected] = useState(null)
    const [loading, setLoading] = useState(true)
    const [toast, setToast] = useState(null)
    const [geoData, setGeoData] = useState(null)

    useEffect(() => {
        // Fetch official Kenya counties GeoJSON
        fetch('/counties.geojson')
            .then(r => r.json())
            .then(data => setGeoData(data))
            .catch(e => console.error('Failed to load county paths', e))

        // Fetch active disasters
        fetch(`${api}/disasters?status=active`)
            .then(r => r.json())
            .then(data => { setDisasters(data); setLoading(false) })
            .catch(() => setLoading(false))

        // Fetch complete county risks for choropleth mapping
        fetch(`${api}/counties/risk`)
            .then(r => r.json())
            .then(data => setCountyRisks(data))
            .catch(e => console.error('Failed to load county risks', e))

        const t = setInterval(() => {
            fetch(`${api}/disasters?status=active`)
                .then(r => r.json())
                .then(setDisasters)
                .catch(() => { })
            fetch(`${api}/counties/risk`)
                .then(r => r.json())
                .then(setCountyRisks)
                .catch(() => { })
        }, 60000)
        return () => clearInterval(t)
    }, [api])

    // Match geometric counties to disasters and risks to create Choropleth
    const getCountyStyle = (feature) => {
        const countyName = feature.properties.shapeName || feature.properties.ADM1_EN

        // Match Risk Score
        const countyRisk = countyRisks.find(c =>
            c.name && countyName &&
            (c.name.toLowerCase().includes(countyName.toLowerCase()) ||
                countyName.toLowerCase().includes(c.name.toLowerCase()))
        )
        const score = countyRisk ? countyRisk.risk_score : 0

        // Determine Color based on Risk Score (0-100) to resemble a beautiful Choropleth Heat Map
        let fillColor = '#0288d1' // Default Safe (Dark Blue)
        if (score >= 80) fillColor = '#b91c1c' // Critical - Dark Red
        else if (score >= 60) fillColor = '#ff5722' // High - Orange Red
        else if (score >= 40) fillColor = '#ff9800' // Medium - Orange
        else if (score >= 20) fillColor = '#ffeb3b' // Low - Yellow
        else if (score > 10) fillColor = '#4fc3f7' // Minimal - Light Blue

        // Find if this county has an active disaster
        const activeDisaster = disasters.find(d =>
            d.county_name && countyName &&
            (d.county_name.toLowerCase().includes(countyName.toLowerCase()) ||
                countyName.toLowerCase().includes(d.county_name.toLowerCase()))
        )

        // Pulsating motion to signify disaster intensity (covered area motion requirement)
        const severityClass = activeDisaster
            ? (activeDisaster.severity === 'High' ? 'pulse-high' : activeDisaster.severity === 'Medium' ? 'pulse-medium' : 'pulse-low')
            : ''

        return {
            fillColor: fillColor,
            weight: 1,
            opacity: 0.8,
            color: '#1e293b', // Subdued dark map border
            fillOpacity: 0.75, // Solid heat map fill
            className: `heatmap-polygon ${severityClass}`
        }
    }

    const showToast = (msg, type = 'success') => {
        setToast({ msg, type })
        setTimeout(() => setToast(null), 3000)
    }

    const resolve = async (id) => {
        await fetch(`${api}/disasters/${id}/resolve`, { method: 'PATCH' })
        setDisasters(prev => prev.filter(d => d.id !== id))
        showToast('✅ Disaster marked as resolved')
    }

    return (
        <div style={{ position: 'relative' }}>
            {/* Choropleth Legend */}
            <div style={{
                display: 'flex', gap: 16, marginBottom: 16, flexWrap: 'wrap', alignItems: 'center'
            }}>
                <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--text-primary)', marginRight: 4 }}>
                    Risk Map:
                </div>
                {[
                    { label: 'Critical (80+)', color: '#b91c1c' },
                    { label: 'High (60+)', color: '#ff5722' },
                    { label: 'Medium (40+)', color: '#ff9800' },
                    { label: 'Low (20+)', color: '#ffeb3b' },
                    { label: 'Minimal', color: '#4fc3f7' },
                    { label: 'Safe', color: '#0288d1' }
                ].map(s => (
                    <div key={s.label} style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 12 }}>
                        <div style={{
                            width: 14, height: 14, borderRadius: 3,
                            background: s.color, border: '1px solid rgba(255,255,255,0.1)',
                            boxShadow: `0 0 6px ${s.color}`
                        }} />
                        <span style={{ color: 'var(--text-secondary)' }}>{s.label}</span>
                    </div>
                ))}

                <div style={{ marginLeft: 'auto', fontSize: 13, color: 'var(--text-muted)' }}>
                    {loading ? '⏳ Updating Matrix...' : `${disasters.length} active disaster${disasters.length !== 1 ? 's' : ''}`}
                </div>
            </div>

            <div className="map-container">
                <MapContainer
                    center={[0.2, 37.9]}
                    zoom={6}
                    style={{ height: '100%', width: '100%' }}
                >
                    <TileLayer
                        url="https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png"
                        attribution='&copy; <a href="https://carto.com/">CARTO</a>'
                    />

                    {/* Regional Choropleth Heatmap Fill */}
                    {geoData && countyRisks.length > 0 && (
                        <GeoJSON
                            data={geoData}
                            style={getCountyStyle}
                            key={JSON.stringify(countyRisks.map(c => c.risk_score)) + JSON.stringify(disasters.map(d => d.id))}
                        />
                    )}

                    {disasters.filter(d => d.lat && d.lng).map(d => (
                        <CircleMarker
                            key={d.id}
                            center={[d.lat, d.lng]}
                            radius={d.severity === 'High' ? 7 : d.severity === 'Medium' ? 5 : 4}
                            pathOptions={{
                                color: '#ffffff', // white border to stand out from heatmap
                                fillColor: SEVERITY_COLOR[d.severity] || '#f59e0b',
                                fillOpacity: 0.9,
                                weight: 2,
                            }}
                            eventHandlers={{ click: () => setSelected(d) }}
                        >
                            <Popup className="kdms-popup">
                                <div style={{
                                    background: '#0a1628',
                                    border: '1px solid rgba(99,158,255,0.2)',
                                    borderRadius: 10,
                                    padding: '14px 16px',
                                    minWidth: 220,
                                    color: '#f0f4ff',
                                    fontFamily: 'Inter, sans-serif',
                                }}>
                                    <div style={{ fontSize: 20, marginBottom: 6 }}>
                                        {TYPE_ICON[d.type] || TYPE_ICON.default} {d.type}
                                    </div>
                                    <div style={{ fontWeight: 700, fontSize: 15, marginBottom: 4 }}>{d.location}</div>
                                    <div style={{ fontSize: 12, color: '#94a3b8', marginBottom: 8 }}>
                                        {d.county_name && <span>📍 {d.county_name} · </span>}
                                        <span style={{ color: SEVERITY_COLOR[d.severity] }}>⚠ {d.severity}</span>
                                    </div>
                                    <div style={{ fontSize: 11, color: '#64748b', marginBottom: 6, display: 'flex', justifyContent: 'space-between' }}>
                                        <span>⏰ {d.reported_at ? new Date(d.reported_at).toLocaleString() : 'Just now'}</span>
                                        <span>Status: {d.status}</span>
                                    </div>
                                    {d.affected_people > 0 && (
                                        <div style={{ fontSize: 13, marginBottom: 6, color: '#CBD5E1' }}>
                                            👥 {d.affected_people.toLocaleString()} affected
                                        </div>
                                    )}
                                    {d.description && (
                                        <div style={{ fontSize: 12, color: '#94a3b8', marginBottom: 10, lineHeight: 1.5 }}>
                                            {d.description}
                                        </div>
                                    )}
                                    <button
                                        onClick={() => resolve(d.id)}
                                        style={{
                                            width: '100%', padding: '7px 12px',
                                            background: 'rgba(16,185,129,0.15)',
                                            border: '1px solid rgba(16,185,129,0.35)',
                                            borderRadius: 7, color: '#10b981',
                                            fontSize: 12, fontWeight: 600,
                                            cursor: 'pointer', fontFamily: 'Inter, sans-serif',
                                        }}
                                    >
                                        ✓ Mark Resolved
                                    </button>
                                </div>
                            </Popup>
                        </CircleMarker>
                    ))}

                    <FitBounds disasters={disasters} />
                </MapContainer>
            </div>

            {
                toast && (
                    <div className={`toast ${toast.type}`}>{toast.msg}</div>
                )
            }
        </div >
    )
}
