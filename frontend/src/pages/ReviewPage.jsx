import React from 'react';
import { ArrowLeft, Save, Flame, Clock, Zap, Beaker, Layers, Activity } from 'lucide-react';

export default function ReviewPage({ data, onReset }) {
    // Fallbacks in case AI extraction missed a section
    const header = data?.header || {};
    const timeAndEnergy = data?.time_and_energy || {};
    const chemComp = data?.chemical_composition || [];
    const scrap = data?.scrap_and_returns || [];
    const alloys = data?.ferro_pure_alloys || [];
    const deox = data?.deoxidants || [];
    const process = data?.process_parameters || {};
    const yieldData = data?.yield_and_dispatch || {};

    const handleSave = () => {
        alert("Metallurgical Data validated and saved to Database!");
        onReset();
    };

    // Reusable card style
    const cardStyle = {
        background: 'white',
        border: '1px solid #e5e7eb',
        borderRadius: '8px',
        padding: '20px',
        boxShadow: '0 1px 3px rgba(0,0,0,0.05)'
    };

    return (
        <div style={{ padding: '30px', fontFamily: 'system-ui, sans-serif', maxWidth: '1400px', margin: '0 auto', backgroundColor: '#f9fafb', minHeight: '100vh' }}>
            {/* Top Navigation & Actions */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '30px' }}>
                <div>
                    <h2 style={{ margin: 0, color: '#111827', fontSize: '24px' }}>Melt Log Validation</h2>
                    <p style={{ margin: '5px 0 0 0', color: '#6b7280' }}>Review extracted induction furnace parameters</p>
                </div>
                <div style={{ display: 'flex', gap: '12px' }}>
                    <button onClick={onReset} style={{ display: 'flex', alignItems: 'center', padding: '10px 16px', background: 'white', border: '1px solid #d1d5db', borderRadius: '6px', cursor: 'pointer', fontWeight: '500' }}>
                        <ArrowLeft size={16} style={{ marginRight: '8px' }} /> Back to Queue
                    </button>
                    <button onClick={handleSave} style={{ display: 'flex', alignItems: 'center', padding: '10px 16px', backgroundColor: '#2563eb', color: 'white', border: 'none', borderRadius: '6px', cursor: 'pointer', fontWeight: '500' }}>
                        <Save size={16} style={{ marginRight: '8px' }} /> Confirm & Export
                    </button>
                </div>
            </div>

            {/* KPI Ribbon */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '20px', marginBottom: '20px' }}>
                {[
                    { label: 'Melt Number', value: header.melt_number, icon: <Flame color="#ef4444" /> },
                    { label: 'Material Grade', value: header.grade, icon: <Layers color="#3b82f6" /> },
                    { label: 'Log Date', value: header.date, icon: <Clock color="#8b5cf6" /> },
                    { label: 'Crucible No', value: header.crucible_no, icon: <Activity color="#10b981" /> }
                ].map((kpi, i) => (
                    <div key={i} style={{ ...cardStyle, display: 'flex', alignItems: 'center', gap: '16px' }}>
                        <div style={{ padding: '12px', background: '#f3f4f6', borderRadius: '8px' }}>{kpi.icon}</div>
                        <div>
                            <p style={{ margin: 0, fontSize: '13px', color: '#6b7280', textTransform: 'uppercase', fontWeight: '600' }}>{kpi.label}</p>
                            <p style={{ margin: 0, fontSize: '20px', fontWeight: 'bold', color: '#111827' }}>{kpi.value || '—'}</p>
                        </div>
                    </div>
                ))}
            </div>

            {/* Main Content Grid */}
            <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '20px' }}>

                {/* Left Column: Chemical Matrix & Materials */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>

                    {/* Chemical Composition Table */}
                    <div style={cardStyle}>
                        <h3 style={{ margin: '0 0 16px 0', display: 'flex', alignItems: 'center', gap: '8px' }}>
                            <Beaker size={20} color="#6366f1" /> Required Chemical Composition (%)
                        </h3>
                        <div style={{ overflowX: 'auto' }}>
                            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '14px', textAlign: 'left' }}>
                                <thead>
                                    <tr style={{ background: '#f8fafc', borderBottom: '2px solid #e2e8f0' }}>
                                        <th style={{ padding: '12px 8px' }}>Element</th>
                                        <th style={{ padding: '12px 8px' }}>Inti Min-Max</th>
                                        <th style={{ padding: '12px 8px' }}>UAPL Min-Max</th>
                                        <th style={{ padding: '12px 8px' }}>Bath Readings</th>
                                        <th style={{ padding: '12px 8px', background: '#eef2ff', color: '#3730a3' }}>Final Sample</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {chemComp.map((row, idx) => (
                                        <tr key={idx} style={{ borderBottom: '1px solid #f1f5f9' }}>
                                            <td style={{ padding: '10px 8px', fontWeight: '600' }}>{row.element}</td>
                                            <td style={{ padding: '10px 8px', color: '#64748b' }}>{row.inti_min} - {row.inti_max}</td>
                                            <td style={{ padding: '10px 8px', color: '#64748b' }}>{row.uapl_min} - {row.uapl_max}</td>
                                            <td style={{ padding: '10px 8px' }}>
                                                {row.bath_readings?.filter(v => v !== null).join(', ') || '—'}
                                            </td>
                                            <td style={{ padding: '10px 8px', fontWeight: 'bold', background: '#f5f7ff', color: '#1e40af' }}>
                                                {row.final_sample ?? '—'}
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </div>

                    {/* Charge & Additions */}
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '16px' }}>
                        {[
                            { title: 'Scrap & Returns', data: scrap },
                            { title: 'Ferro/Pure Alloys', data: alloys },
                            { title: 'Deoxidants', data: deox }
                        ].map((section, idx) => (
                            <div key={idx} style={{ ...cardStyle, padding: '16px' }}>
                                <h4 style={{ margin: '0 0 12px 0', fontSize: '15px', color: '#374151' }}>{section.title}</h4>
                                <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
                                    {section.data.map((item, i) => (
                                        <li key={i} style={{ display: 'flex', justifyContent: 'space-between', padding: '6px 0', borderBottom: '1px dashed #e5e7eb', fontSize: '14px' }}>
                                            <span>{item.material_name}</span>
                                            <span style={{ fontWeight: '600' }}>{item.quantity_kgs} kg</span>
                                        </li>
                                    ))}
                                </ul>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Right Column: Time, Process, Yield */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>

                    {/* Time & Energy */}
                    <div style={cardStyle}>
                        <h3 style={{ margin: '0 0 16px 0', display: 'flex', alignItems: 'center', gap: '8px' }}>
                            <Zap size={20} color="#eab308" /> Time & Energy Consumed
                        </h3>
                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', fontSize: '14px' }}>
                            <div style={{ color: '#6b7280' }}>Furnace Started:</div><div style={{ fontWeight: '500' }}>{timeAndEnergy.furnace_started_at || '—'}</div>
                            <div style={{ color: '#6b7280' }}>Melt Tapped:</div><div style={{ fontWeight: '500' }}>{timeAndEnergy.melt_tapped_at || '—'}</div>
                            <div style={{ color: '#6b7280' }}>Total Time:</div><div style={{ fontWeight: '500' }}>{timeAndEnergy.total_time_consumed || '—'}</div>
                            <div style={{ gridColumn: 'span 2', height: '1px', background: '#e5e7eb', margin: '8px 0' }}></div>
                            <div style={{ color: '#6b7280' }}>Power Total:</div><div style={{ fontWeight: 'bold', color: '#047857' }}>{timeAndEnergy.power_total_units ? `${timeAndEnergy.power_total_units} Units` : '—'}</div>
                        </div>
                    </div>

                    {/* Process Parameters */}
                    <div style={cardStyle}>
                        <h3 style={{ margin: '0 0 16px 0', fontSize: '18px' }}>Process Parameters</h3>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', fontSize: '14px' }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between' }}><span style={{ color: '#6b7280' }}>Tapping Temp:</span> <strong>{process.tapping_temp_c || '—'}</strong></div>
                            <div style={{ display: 'flex', justifyContent: 'space-between' }}><span style={{ color: '#6b7280' }}>Pouring Temp:</span> <strong>{process.pouring_temp_c || '—'}</strong></div>
                            <div style={{ display: 'flex', justifyContent: 'space-between' }}><span style={{ color: '#6b7280' }}>Slag Condition:</span> <strong>{process.slag_condition || '—'}</strong></div>
                            <div style={{ display: 'flex', justifyContent: 'space-between' }}><span style={{ color: '#6b7280' }}>Lining Condition:</span> <strong>{process.lining_condition || '—'}</strong></div>
                            <div style={{ display: 'flex', justifyContent: 'space-between' }}><span style={{ color: '#6b7280' }}>Dissolved Gas:</span> <strong>{process.dissolved_gas_level || '—'}</strong></div>
                        </div>
                    </div>

                    {/* Yield & Dispatch */}
                    <div style={{ ...cardStyle, background: '#f0fdf4', borderColor: '#bbf7d0' }}>
                        <h3 style={{ margin: '0 0 16px 0', fontSize: '18px', color: '#166534' }}>Yield & Dispatch</h3>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', fontSize: '14px', color: '#166534' }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between' }}><span>Total Metal Tapped:</span> <strong style={{ fontSize: '16px' }}>{yieldData.total_metal_tapped_kgs ? `${yieldData.total_metal_tapped_kgs} kg` : '—'}</strong></div>
                            <div style={{ display: 'flex', justifyContent: 'space-between' }}><span>Total Charges:</span> <strong>{yieldData.total_charges_kgs ? `${yieldData.total_charges_kgs} kg` : '—'}</strong></div>
                            <div style={{ display: 'flex', justifyContent: 'space-between' }}><span>Moulds Poured:</span> <strong>{yieldData.no_of_moulds_poured || '—'}</strong></div>
                        </div>
                    </div>

                </div>
            </div>

            {/* QC Remarks Footer */}
            {yieldData.qc_remarks && (
                <div style={{ marginTop: '20px', padding: '16px 20px', background: '#fffbeb', borderLeft: '4px solid #f59e0b', borderRadius: '4px' }}>
                    <h4 style={{ margin: '0 0 8px 0', color: '#b45309' }}>QC Remarks & Observations</h4>
                    <p style={{ margin: 0, color: '#78350f', fontStyle: 'italic' }}>"{yieldData.qc_remarks}"</p>
                </div>
            )}
        </div>
    );
}