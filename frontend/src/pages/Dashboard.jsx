import React, { useState, useEffect } from 'react';
import {
  UploadCloud, FileText, CheckCircle, AlertCircle, Calendar, Flame,
  Thermometer, Scale, Activity, ArrowRight, Clock, Info, Layers3,
  Database, TrendingUp, Award, Zap, BarChart3, History, TrendingDown,
  Download, Beaker, Layers
} from 'lucide-react';
import {
  ResponsiveContainer, ScatterChart, Scatter, XAxis, YAxis, ZAxis,
  CartesianGrid, Tooltip, Legend, LineChart, Line, BarChart, Bar,
  AreaChart, Area, ReferenceLine, ComposedChart
} from 'recharts';
import { documentApi } from '../services/api';

// Harmonious industrial color palette
const HEAT_COLORS = [
  "#22d3ee", "#818cf8", "#fbbf24", "#34d399", "#f87171",
  "#a78bfa", "#38bdf8", "#fb923c", "#2dd4bf", "#ec4899"
];

// Custom Glassmorphic Tooltip for Recharts
const CustomTooltip = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-slate-950/90 backdrop-blur-md border border-slate-800 rounded-xl p-3 shadow-2xl">
        <p className="text-slate-400 text-[10px] uppercase tracking-wider font-bold mb-1.5">{label}</p>
        {payload.map((p, idx) => (
          <div key={idx} className="flex items-center gap-2.5 text-xs font-semibold py-0.5">
            <span className="w-2.5 h-2.5 rounded-full shrink-0" style={{ backgroundColor: p.color || p.stroke || p.fill }} />
            <span className="text-slate-300 font-medium">{p.name}:</span>
            <span style={{ color: p.color || p.stroke || p.fill }} className="font-mono">
              {typeof p.value === 'number' ? p.value.toLocaleString() : p.value}
            </span>
          </div>
        ))}
      </div>
    );
  }
  return null;
};

export default function Dashboard() {
  const [activeTab, setActiveTab] = useState('ingest'); // 'ingest' or 'historical'

  // File upload states
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [dragActive, setDragActive] = useState(false);

  // States for active document analytics
  const [chemRows, setChemRows] = useState([]);
  const [chargeData, setChargeData] = useState([]);

  // Historical database analytics states
  const [historicalData, setHistoricalData] = useState([]);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [historyError, setHistoryError] = useState(null);
  const [exporting, setExporting] = useState(false);

  // Process currently extracted document (Tab 1)
  useEffect(() => {
    if (!result) {
      setChemRows([]);
      setChargeData([]);
      return;
    }

    // Parse chemical composition for charts
    const chemComp = result.chemical_composition || [];
    setChemRows(chemComp);

    // Parse charge additions for charts (mapping furnace and ladle weights)
    const scrap = result.scrap_and_returns || [];
    const alloys = result.ferro_pure_alloys || [];
    const deox = result.deoxidants || [];

    const combinedCharges = [
      ...scrap.map(s => ({ category: 'Scrap/Returns', name: s.material_name, weight: s.quantity_kgs || 0, ladle: s.quantity_ladle_kgs || 0 })),
      ...alloys.map(a => ({ category: 'Alloys', name: a.material_name, weight: a.quantity_kgs || 0, ladle: a.quantity_ladle_kgs || 0 })),
      ...deox.map(d => ({ category: 'Deoxidants', name: d.material_name, weight: d.quantity_kgs || 0, ladle: d.quantity_ladle_kgs || 0 }))
    ].filter(item => item.weight > 0 || item.ladle > 0);

    setChargeData(combinedCharges);
  }, [result]);

  // Load and process historical heats from Database (Tab 2)
  const fetchHistoricalData = async () => {
    setHistoryLoading(true);
    setHistoryError(null);
    try {
      const data = await documentApi.getAllDocuments();
      if (data && data.length > 0) {
        const parsedHistory = data.map((doc, index) => {
          const extracted = doc.extracted_data || doc;
          const header = extracted.header || {};
          const time = extracted.time_and_energy || {};
          const yieldData = extracted.yield_and_dispatch || {};
          const process = extracted.process_parameters || {};

          return {
            id: index,
            meltNo: header.melt_number || `Unknown-${index}`,
            grade: header.grade || 'N/A',
            powerUnits: parseFloat(time.power_total_units) || 0,
            totalMetal: parseFloat(yieldData.total_metal_tapped_kgs) || 0,
            tappingTemp: parseFloat((process.tapping_temp_c || "0").replace(/[^0-9.]/g, "")) || 0,
            date: header.date || 'N/A'
          };
        }).filter(h => h.meltNo !== 'Unknown' && h.powerUnits > 0);

        // Sort by Date or ID
        setHistoricalData(parsedHistory.slice(-20)); // Keep last 20 heats for clean charts
      } else {
        setHistoricalData([]);
      }
    } catch (err) {
      console.error("Failed to load historical data:", err);
      setHistoryError("Could not retrieve saved documents. Make sure the database service is online.");
    } finally {
      setHistoryLoading(false);
    }
  };

  useEffect(() => {
    if (activeTab === 'historical') {
      fetchHistoricalData();
    }
  }, [activeTab]);

  const handleExport = async () => {
    setExporting(true);
    try {
      const blob = await documentApi.exportDocuments();
      const url = window.URL.createObjectURL(new Blob([blob]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', 'induction_furnace_logs.xlsx');
      document.body.appendChild(link);
      link.click();
      link.parentNode.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (err) {
      alert("Failed to export Excel file: " + (err.message || "Unknown error"));
    } finally {
      setExporting(false);
    }
  };

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setError(null);
    }
  };

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") setDragActive(true);
    else if (e.type === "dragleave") setDragActive(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      setFile(e.dataTransfer.files[0]);
      setError(null);
    }
  };

  const handleUpload = async () => {
    if (!file) {
      setError("Please select a file first.");
      return;
    }
    setLoading(true);
    setError(null);
    setResult(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch('http://127.0.0.1:8000/api/v1/documents/process', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) throw new Error(`Server responded with status: ${response.status}`);
      const data = await response.json();
      if (data.error) throw new Error(data.error);

      setResult(data.data);
    } catch (err) {
      setError(err.message || "Failed to process document.");
    } finally {
      setLoading(false);
    }
  };

  // Safe destructuring of result for UI
  const header = result?.header || {};
  const timeAndEnergy = result?.time_and_energy || {};
  const furnaceReadings = timeAndEnergy.furnace_readings || [];
  const processParams = result?.process_parameters || {};
  const yieldData = result?.yield_and_dispatch || {};

  return (
    <div className="p-4 sm:p-8 space-y-8 max-w-[1600px] mx-auto z-10 relative">
      <style dangerouslySetInnerHTML={{
        __html: `
        .custom-scrollbar::-webkit-scrollbar { height: 10px; }
        .custom-scrollbar::-webkit-scrollbar-track { background: #0f172a; border-radius: 6px; }
        .custom-scrollbar::-webkit-scrollbar-thumb { background: #334155; border-radius: 6px; border: 2px solid #0f172a; }
        .custom-scrollbar::-webkit-scrollbar-thumb:hover { background: #475569; }
        @keyframes laser-scan {
          0%, 100% { top: 0%; opacity: 0.8; }
          50% { top: 100%; opacity: 0.3; }
        }
        .animate-laser { animation: laser-scan 3s ease-in-out infinite; }
      `}} />

      {/* Header & Page Title */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 border-b border-slate-800 pb-5">
        <div>
          <h1 className="text-3xl font-extrabold bg-gradient-to-r from-cyan-400 via-indigo-400 to-purple-400 bg-clip-text text-transparent">
            Induction Furnace Intelligence
          </h1>
          <p className="text-slate-400 text-sm mt-1">
            Real-time metallurgical data extraction, chemical validation, and power analytics.
          </p>
        </div>

        <div className="flex items-center gap-2.5 px-4 py-2 bg-slate-900/60 border border-slate-800/80 rounded-xl shadow-inner">
          <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 shadow-[0_0_8px_#10b981] animate-pulse" />
          <span className="text-xs text-slate-300 font-semibold flex items-center gap-1">
            <Database size={13} className="text-cyan-400" /> Database Connected
          </span>
        </div>
      </div>

      {/* Tab Switcher */}
      <div className="flex bg-slate-950/60 p-1.5 border border-slate-850 rounded-2xl w-full sm:w-[480px] shadow-lg shadow-slate-950/40">
        <button
          onClick={() => setActiveTab('ingest')}
          className={`flex-1 flex items-center justify-center gap-2 py-3.5 px-5 rounded-xl text-xs font-extrabold uppercase tracking-wider transition-all duration-300 ${activeTab === 'ingest' ? 'bg-gradient-to-r from-cyan-500 to-indigo-500 text-slate-950 shadow-md font-sans' : 'text-slate-400 hover:text-slate-200'}`}
        >
          <Layers3 size={15} />
          <span>Furnace Ingestion</span>
        </button>
        <button
          onClick={() => setActiveTab('historical')}
          className={`flex-1 flex items-center justify-center gap-2 py-3.5 px-5 rounded-xl text-xs font-extrabold uppercase tracking-wider transition-all duration-300 ${activeTab === 'historical' ? 'bg-gradient-to-r from-cyan-500 to-indigo-500 text-slate-950 shadow-md font-sans' : 'text-slate-400 hover:text-slate-200'}`}
        >
          <History size={15} />
          <span>Historical Analytics</span>
        </button>
      </div>

      {/* TAB 1: Ingestion & Current Sheet Analytics */}
      {activeTab === 'ingest' && (
        <div className="space-y-8 animate-fade-in">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* Upload Panel */}
            <div className="lg:col-span-2 bg-slate-900/60 backdrop-blur-md p-6 rounded-2xl border border-slate-800 shadow-xl flex flex-col justify-between">
              <div>
                <div className="flex items-center gap-3 mb-4">
                  <Flame className="text-cyan-400" size={22} />
                  <h2 className="text-lg font-bold text-slate-100">Log Sheet Parser</h2>
                </div>
                <div
                  onDragEnter={handleDrag} onDragOver={handleDrag} onDragLeave={handleDrag} onDrop={handleDrop}
                  className={`relative border-2 border-dashed rounded-xl p-8 flex flex-col items-center justify-center transition-all duration-300 ${dragActive ? 'border-cyan-400 bg-cyan-950/20 scale-[0.99]' : 'border-slate-800 bg-slate-950/40 hover:border-slate-700 hover:bg-slate-900/20'}`}
                >
                  <input type="file" onChange={handleFileChange} accept=".pdf,.jpg,.jpeg,.png" className="absolute inset-0 w-full h-full opacity-0 cursor-pointer" />
                  <div className="p-3.5 bg-slate-900 rounded-xl text-slate-400 mb-4 border border-slate-800 shadow-md">
                    <UploadCloud size={28} className="text-cyan-400" />
                  </div>
                  <p className="text-slate-200 text-xs font-semibold mb-1">{file ? file.name : "Drag & Drop files here"}</p>
                </div>
              </div>
              <div className="mt-6 flex justify-end">
                <button
                  onClick={handleUpload} disabled={loading || !file}
                  className={`w-full sm:w-auto px-8 py-3 rounded-xl font-bold text-xs uppercase tracking-wider transition-all duration-300 flex items-center justify-center gap-2 shadow-lg ${loading || !file ? 'bg-slate-800 text-slate-500 cursor-not-allowed border border-slate-800' : 'bg-gradient-to-r from-cyan-500 to-indigo-500 text-slate-950 hover:scale-[1.02] shadow-cyan-500/10'}`}
                >
                  {loading ? <><span className="w-3.5 h-3.5 border-2 border-slate-950 border-t-transparent rounded-full animate-spin" /><span>Extracting...</span></> : <><Database size={14} /><span>Parse to Database</span></>}
                </button>
              </div>
            </div>

            {/* Live Status Panel */}
            <div className="bg-slate-900/60 backdrop-blur-md p-6 rounded-2xl border border-slate-800 shadow-xl relative overflow-hidden flex flex-col justify-between">
              {loading && <div className="absolute left-0 w-full h-1 bg-gradient-to-r from-transparent via-cyan-400 to-transparent shadow-[0_0_15px_#22d3ee] animate-laser z-20" />}
              <div>
                <div className="flex items-center gap-3 mb-4">
                  <Activity className="text-indigo-400" size={22} />
                  <h2 className="text-lg font-bold text-slate-100">Telemetry Stream</h2>
                </div>
                {loading ? (
                  <div className="py-10 flex flex-col items-center justify-center text-center space-y-4">
                    <div className="relative w-16 h-16"><div className="absolute inset-0 rounded-full border-4 border-slate-800 border-t-cyan-400 animate-spin" /><div className="absolute inset-2 rounded-full border-4 border-slate-800 border-t-indigo-400 animate-spin" style={{ animationDirection: 'reverse' }} /></div>
                    <h3 className="text-slate-200 text-xs font-bold uppercase tracking-wider">Vision Pipeline Active</h3>
                  </div>
                ) : result ? (
                  <div className="space-y-4 py-1">
                    <div className="p-4 rounded-xl bg-slate-950/85 border border-slate-800 space-y-3">
                      <div className="flex items-center gap-2 text-emerald-400 text-xs font-bold border-b border-slate-800 pb-2 uppercase"><CheckCircle size={14} /> Inference Success</div>
                      <div className="grid grid-cols-2 gap-4 text-xs">
                        <div><span className="text-slate-500 block uppercase font-bold text-[10px]">Melt Number</span><strong className="text-cyan-400 text-base font-mono">{header.melt_number || 'N/A'}</strong></div>
                        <div><span className="text-slate-500 block uppercase font-bold text-[10px]">Elements Read</span><strong className="text-slate-200 text-base font-mono">{chemRows.length} rows</strong></div>
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="py-10 text-center text-slate-500 text-xs uppercase font-bold tracking-wider">Ready for Log Sheet</div>
                )}
              </div>
              {error && <div className="mt-4 p-4 bg-rose-950/20 border border-rose-900/30 text-rose-300 rounded-xl text-xs font-bold flex gap-2"><AlertCircle size={16} />{error}</div>}
            </div>
          </div>

          {/* Current Ingested Analytics */}
          {result && (
            <div className="space-y-8 animate-fade-in">
              {/* Premium KPI Layer */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {[
                  { label: 'Grade Target', value: header.grade, icon: <Layers color="#3b82f6" /> },
                  { label: 'Furnace Run Time', value: timeAndEnergy.total_time_consumed, icon: <Clock color="#8b5cf6" /> },
                  { label: 'Power Consumption', value: timeAndEnergy.power_total_units ? `${timeAndEnergy.power_total_units} Units` : null, icon: <Zap color="#eab308" /> },
                  { label: 'Crucible Config', value: header.crucible_no ? `Crucible ${header.crucible_no}` : null, icon: <Activity color="#10b981" /> }
                ].map((kpi, i) => (
                  <div key={i} className="bg-gradient-to-br from-slate-900/90 to-slate-950/70 p-4 rounded-xl border border-slate-800 flex items-center gap-4 shadow-xl">
                    <div className="p-3 bg-slate-950 rounded-lg border border-slate-800">{kpi.icon}</div>
                    <div>
                      <p className="text-[10px] text-slate-500 uppercase font-bold tracking-wider">{kpi.label}</p>
                      <p className="text-lg font-bold text-slate-200 font-mono">{kpi.value || '—'}</p>
                    </div>
                  </div>
                ))}
              </div>

              {/* Chemical Composition Grid */}
              <div className="bg-slate-900/60 backdrop-blur-md rounded-2xl border border-slate-800 shadow-xl overflow-hidden mt-8">
                <div className="p-6 border-b border-slate-800 flex justify-between items-center">
                  <h3 className="text-lg font-bold text-slate-100 flex items-center gap-2"><Beaker size={20} className="text-indigo-400" /> Required Chemical Composition Matrix (%)</h3>
                </div>
                <div className="overflow-x-auto custom-scrollbar">
                  <table className="min-w-full divide-y divide-slate-800 text-xs font-semibold">
                    <thead className="bg-slate-950/60 text-slate-500 uppercase font-bold text-[9px] tracking-wider">
                      <tr>
                        <th className="px-6 py-4 text-left border-r border-slate-900">Element</th>
                        <th className="px-6 py-4 text-left border-r border-slate-900">Inti Min-Max</th>
                        <th className="px-6 py-4 text-left border-r border-slate-900">UAPL Min-Max</th>
                        <th className="px-6 py-4 text-left border-r border-slate-900">Bath Progressions</th>
                        <th className="px-6 py-4 text-right text-indigo-400">Final Validation Sample</th>
                      </tr>
                    </thead>
                    <tbody className="bg-slate-950/10 divide-y divide-slate-800/40 text-slate-300">
                      {chemRows.map((row, idx) => (
                        <tr key={idx} className="hover:bg-slate-900/40 transition-colors">
                          <td className="px-6 py-3.5 text-cyan-400 font-bold border-r border-slate-900 text-sm">{row.element}</td>
                          <td className="px-6 py-3.5 text-slate-400 border-r border-slate-900">{row.inti_min ?? '—'} to {row.inti_max ?? '—'}</td>
                          <td className="px-6 py-3.5 text-slate-400 border-r border-slate-900">{row.uapl_min ?? '—'} to {row.uapl_max ?? '—'}</td>
                          <td className="px-6 py-3.5 text-slate-500 font-mono border-r border-slate-900 tracking-widest">{row.bath_readings?.filter(v => v !== null).join('  →  ') || '—'}</td>
                          <td className="px-6 py-3.5 text-right text-emerald-400 font-mono font-bold text-sm bg-emerald-950/5">{row.final_sample ?? '—'}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Furnace Readings Table */}
              <div className="bg-slate-900/60 backdrop-blur-md rounded-2xl border border-slate-800 shadow-xl overflow-hidden mt-8">
                <div className="p-6 border-b border-slate-800 flex justify-between items-center">
                  <h3 className="text-lg font-bold text-slate-100 flex items-center gap-2"><Flame size={20} className="text-orange-400" /> Furnace Power Readings</h3>
                </div>
                <div className="overflow-x-auto custom-scrollbar">
                  <table className="min-w-full divide-y divide-slate-800 text-xs font-semibold">
                    <thead className="bg-slate-950/60 text-slate-500 uppercase font-bold text-[9px] tracking-wider">
                      <tr>
                        <th className="px-6 py-4 text-left border-r border-slate-900">Time (Hrs)</th>
                        <th className="px-6 py-4 text-center border-r border-slate-900">Freq</th>
                        <th className="px-6 py-4 text-center border-r border-slate-900">KW</th>
                        <th className="px-6 py-4 text-center border-r border-slate-900">Voltage</th>
                        <th className="px-6 py-4 text-center border-r border-slate-900">Inlet Temp</th>
                        <th className="px-6 py-4 text-center border-r border-slate-900">Outlet Temp</th>
                        <th className="px-6 py-4 text-center text-cyan-400">GLD</th>
                      </tr>
                    </thead>
                    <tbody className="bg-slate-950/10 divide-y divide-slate-800/40 text-slate-300">
                      {furnaceReadings.map((row, idx) => (
                        <tr key={idx} className="hover:bg-slate-900/40 transition-colors">
                          <td className="px-6 py-3.5 text-slate-200 font-bold border-r border-slate-900">{row.time_hrs || '—'}</td>
                          <td className="px-6 py-3.5 text-center font-mono border-r border-slate-900">{row.freq || '—'}</td>
                          <td className="px-6 py-3.5 text-center font-mono text-amber-400 border-r border-slate-900">{row.kw || '—'}</td>
                          <td className="px-6 py-3.5 text-center font-mono text-indigo-400 border-r border-slate-900">{row.voltage || '—'}</td>
                          <td className="px-6 py-3.5 text-center font-mono border-r border-slate-900">{row.inlet || '—'}</td>
                          <td className="px-6 py-3.5 text-center font-mono border-r border-slate-900">{row.outlet || '—'}</td>
                          <td className="px-6 py-3.5 text-center font-mono text-cyan-400 font-bold bg-cyan-950/5">{row.gld || '—'}</td>
                        </tr>
                      ))}
                      {furnaceReadings.length === 0 && (
                        <tr><td colSpan="7" className="px-6 py-8 text-center text-slate-600">No furnace readings detected.</td></tr>
                      )}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* PAGE 2: Extracted Pouring Details Table */}
              <div className="bg-slate-900/60 backdrop-blur-md rounded-2xl border border-slate-800 shadow-xl overflow-hidden mt-8">
                <div className="p-6 border-b border-slate-800 flex justify-between items-center">
                  <h3 className="text-lg font-bold text-slate-100 flex items-center gap-2">
                    <Scale size={20} className="text-emerald-400" /> Page 2: Poured Weight Details
                  </h3>
                  <div className="px-3 py-1 rounded bg-slate-950 border border-slate-800 text-[10px] text-slate-400 uppercase font-bold tracking-wider">
                    {result.pouring_table?.length || 0} Items Cast
                  </div>
                </div>
                <div className="overflow-x-auto custom-scrollbar">
                  <table className="min-w-full divide-y divide-slate-800 text-xs font-semibold">
                    <thead className="bg-slate-950/60 text-slate-500 uppercase font-bold text-[9px] tracking-wider">
                      <tr>
                        <th className="px-6 py-4 text-left border-r border-slate-900">#</th>
                        <th className="px-6 py-4 text-left border-r border-slate-900 w-1/2">Item Description</th>
                        <th className="px-6 py-4 text-center border-r border-slate-900">Quantity</th>
                        <th className="px-6 py-4 text-right border-r border-slate-900 text-slate-400">Planned Weight (kg)</th>
                        <th className="px-6 py-4 text-right text-emerald-400">Actual Poured (kg)</th>
                      </tr>
                    </thead>
                    <tbody className="bg-slate-950/10 divide-y divide-slate-800/40 text-slate-300">
                      {result.pouring_table && result.pouring_table.length > 0 ? (
                        result.pouring_table.map((row, idx) => (
                          <tr key={idx} className="hover:bg-slate-900/40 transition-colors">
                            <td className="px-6 py-3.5 text-slate-600 font-bold border-r border-slate-900">{idx + 1}</td>
                            <td className="px-6 py-3.5 font-bold text-slate-200 border-r border-slate-900">{row.item_description || '—'}</td>
                            <td className="px-6 py-3.5 text-center font-mono text-cyan-400 border-r border-slate-900">{row.quantity || '—'}</td>
                            <td className="px-6 py-3.5 text-right font-mono text-slate-400 border-r border-slate-900">{row.planned_weight_kg || '—'}</td>
                            <td className="px-6 py-3.5 text-right font-mono text-emerald-400 font-bold bg-emerald-950/5">{row.poured_weight_kg || '—'}</td>
                          </tr>
                        ))
                      ) : (
                        <tr>
                          <td colSpan="5" className="px-6 py-8 text-center text-slate-600">No pouring records detected on Page 2.</td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Data Visualization Dashboard */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mt-8">

                {/* Process Parameters & Approvals */}
                <div className="bg-slate-900/60 p-6 rounded-2xl border border-slate-800 shadow-xl flex flex-col justify-between">
                  <div>
                    <div className="flex items-center gap-2 mb-4 border-b border-slate-850 pb-2">
                      <h3 className="text-base font-bold text-slate-200">Process Parameters & Approvals</h3>
                      <span className="ml-auto text-slate-500 text-xs font-bold uppercase tracking-wider">Quality Control</span>
                    </div>
                    <div className="grid grid-cols-2 lg:grid-cols-3 gap-4 mt-6">
                      <div className="p-3 bg-slate-950/50 rounded-xl border border-slate-800">
                        <span className="block text-[10px] uppercase text-slate-500 font-bold mb-1">Tapping Temp</span>
                        <span className="text-lg font-mono text-amber-400">{processParams.tapping_temp_c || '—'}</span>
                      </div>
                      <div className="p-3 bg-slate-950/50 rounded-xl border border-slate-800">
                        <span className="block text-[10px] uppercase text-slate-500 font-bold mb-1">Pouring Temp</span>
                        <span className="text-lg font-mono text-amber-500">{processParams.pouring_temp_c || '—'}</span>
                      </div>
                      <div className="p-3 bg-slate-950/50 rounded-xl border border-slate-800">
                        <span className="block text-[10px] uppercase text-slate-500 font-bold mb-1">Lining Condition</span>
                        <span className="text-sm font-semibold text-emerald-400">{processParams.furnace_lining_condition || '—'}</span>
                      </div>

                      <div className="p-3 bg-slate-950/50 rounded-xl border border-slate-800 lg:col-span-3 flex justify-between items-center">
                        <div>
                          <span className="block text-[10px] uppercase text-slate-500 font-bold mb-1">Total Metal Tapped</span>
                          <span className="text-xl font-mono text-cyan-400">{yieldData.total_metal_tapped_kgs || '—'} kg</span>
                        </div>
                        <div className="text-center border-l border-r border-slate-800 px-4">
                          <span className="block text-[10px] uppercase text-slate-500 font-bold mb-1">Total Charges</span>
                          <span className="text-lg font-mono text-slate-300">{yieldData.total_charges_kgs || '—'} kg</span>
                        </div>
                        <div className="text-right">
                          <span className="block text-[10px] uppercase text-slate-500 font-bold mb-1">Extra Metal</span>
                          <span className="text-lg font-mono text-rose-400">{yieldData.extra_metal_kgs || '—'} kg</span>
                        </div>
                      </div>

                      <div className="p-3 bg-slate-950/50 rounded-xl border border-slate-800 lg:col-span-3 grid grid-cols-2 text-xs text-slate-400 font-semibold gap-2">
                        <div><strong>QC Incharge:</strong> <span className="text-slate-200">{yieldData.qc_incharge || '—'}</span></div>
                        <div><strong>Melting Incharge:</strong> <span className="text-slate-200">{yieldData.melting_incharge || '—'}</span></div>
                        <div><strong>FIC Charge Hand:</strong> <span className="text-slate-200">{yieldData.fic_charge_hand || '—'}</span></div>
                        <div><strong>Spillage Metal:</strong> <span className="text-slate-200 font-mono">{yieldData.spilage_metal_kgs || '0'} kg</span></div>
                        <div><strong>Tags Punched/Checked:</strong> <span className="text-slate-200">{processParams.tags_punched || '—'} / {processParams.hind_tags_checked || '—'}</span></div>
                        <div><strong>Tags Discarded:</strong> <span className="text-slate-200">{yieldData.tags_discard || '—'}</span></div>
                      </div>

                      {timeAndEnergy.sample_times && timeAndEnergy.sample_times.length > 0 && (
                        <div className="p-3 bg-slate-950/50 rounded-xl border border-slate-800 lg:col-span-3">
                          <span className="block text-[10px] uppercase text-slate-500 font-bold mb-1.5">Chemical Sampling Intervals</span>
                          <div className="flex flex-wrap items-center gap-2 text-xs font-semibold font-mono">
                            {timeAndEnergy.sample_times.map((t, idx) => (
                              <React.Fragment key={idx}>
                                {idx > 0 && <span className="text-slate-700 font-sans">→</span>}
                                <span className="px-2 py-0.5 bg-slate-900 border border-slate-800 text-cyan-400 rounded-md">{t}</span>
                              </React.Fragment>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                  {yieldData.qc_remarks && (
                    <div className="mt-4 p-3 bg-amber-950/20 border border-amber-900/30 rounded-xl text-[11px] text-amber-400/80 font-mono italic">
                      " {yieldData.qc_remarks} "
                    </div>
                  )}
                </div>

                {/* Charge Additions Chart */}
                <div className="bg-slate-900/60 p-6 rounded-2xl border border-slate-800 shadow-xl flex flex-col justify-between">
                  <div>
                    <div className="flex items-center gap-2 mb-4 border-b border-slate-850 pb-2">
                      <h3 className="text-base font-bold text-slate-200">Charge Additions Breakdown</h3>
                      <span className="ml-auto text-slate-500 text-xs font-bold uppercase tracking-wider">Furnace vs Ladle</span>
                    </div>
                    {/* The conditional render fixes the Recharts width/height warning */}
                    {chargeData && chargeData.length > 0 ? (
                      <div className="h-[280px] w-full mt-3">
                        <ResponsiveContainer width="100%" height="100%" minWidth={0} minHeight={0}>
                          <BarChart data={chargeData} layout="vertical" margin={{ top: 5, right: 30, bottom: 5, left: 40 }}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" horizontal={false} />
                            <XAxis type="number" stroke="#475569" tick={{ fontSize: 10, fill: '#64748b' }} />
                            <YAxis type="category" dataKey="name" stroke="#475569" tick={{ fontSize: 10, fill: '#cbd5e1' }} />
                            <Tooltip content={<CustomTooltip />} cursor={{ fill: '#1e293b', opacity: 0.4 }} />
                            <Legend wrapperStyle={{ fontSize: 11, paddingTop: 10 }} />
                            <Bar dataKey="weight" name="Furnace (kg)" stackId="a" fill="#818cf8" radius={[0, 0, 0, 0]} />
                            <Bar dataKey="ladle" name="Ladle (kg)" stackId="a" fill="#34d399" radius={[0, 4, 4, 0]} />
                          </BarChart>
                        </ResponsiveContainer>
                      </div>
                    ) : (
                      <div className="flex items-center justify-center h-[280px] text-slate-500 text-xs">
                        No charge additions detected
                      </div>
                    )}
                  </div>
                </div>
              </div>

              {/* Charge Additions Detailed Tables */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-8 animate-fade-in">
                {[
                  { title: 'Scrap & Returns', data: result.scrap_and_returns || [], color: 'text-indigo-400' },
                  { title: 'Ferro & Pure Alloys', data: result.ferro_pure_alloys || [], color: 'text-amber-400' },
                  { title: 'Deoxidants', data: result.deoxidants || [], color: 'text-emerald-400' }
                ].map((section, idx) => (
                  <div key={idx} className="bg-slate-900/60 backdrop-blur-md p-6 rounded-2xl border border-slate-800 shadow-xl flex flex-col justify-between">
                    <div>
                      <div className="flex items-center justify-between border-b border-slate-850 pb-3 mb-4">
                        <h3 className={`text-sm font-bold ${section.color}`}>{section.title}</h3>
                        <span className="text-slate-500 text-[10px] uppercase font-bold tracking-wider">{section.data.length} items</span>
                      </div>
                      {section.data.length > 0 ? (
                        <div className="divide-y divide-slate-800/40 text-xs">
                          {section.data.map((item, i) => (
                            <div key={i} className="flex justify-between items-center py-2.5">
                              <span className="text-slate-300 font-semibold">{item.material_name}</span>
                              <div className="text-right font-mono font-semibold">
                                {item.quantity_kgs > 0 && (
                                  <span className="text-slate-200 block text-xs">
                                    {item.quantity_kgs} kg <span className="text-[10px] text-slate-500 font-sans">Furnace</span>
                                  </span>
                                )}
                                {item.quantity_ladle_kgs > 0 && (
                                  <span className="text-cyan-400 block text-xs">
                                    {item.quantity_ladle_kgs} kg <span className="text-[10px] text-slate-500 font-sans">Ladle</span>
                                  </span>
                                )}
                              </div>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <div className="py-6 text-center text-slate-500 text-xs font-semibold">
                          No additions detected
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* TAB 2: Historical Multi-Heat Analytics */}
      {activeTab === 'historical' && (
        <div className="space-y-8 animate-fade-in">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-3">
            <div className="flex items-center gap-2.5">
              <History className="text-cyan-400" size={22} />
              <h2 className="text-xl font-bold text-slate-100">Historical Furnace Analytics</h2>
            </div>
            <button onClick={handleExport} disabled={exporting} className={`px-4 py-2 rounded-xl text-[11px] font-extrabold uppercase transition-all duration-300 flex items-center gap-2 shadow-lg ${exporting ? 'bg-slate-800 text-slate-600 cursor-not-allowed' : 'bg-gradient-to-r from-emerald-500 to-teal-500 text-slate-950 hover:scale-[1.03]'}`}>
              {exporting ? <><span className="w-3 h-3 border-2 border-slate-950 border-t-transparent rounded-full animate-spin" /><span>Exporting...</span></> : <><Download size={14} /><span>Export Excel</span></>}
            </button>
          </div>

          {historyLoading ? (
            <div className="py-24 text-center"><div className="w-10 h-10 rounded-full border-4 border-slate-800 border-t-cyan-400 animate-spin mx-auto mb-4" /><p className="text-slate-400 text-xs font-bold uppercase">Loading documents...</p></div>
          ) : historicalData.length === 0 ? (
            <div className="py-20 text-center bg-slate-900/40 border border-slate-850 rounded-2xl p-8"><Database size={44} className="text-slate-700 mb-4 mx-auto" /><h3 className="text-slate-200 text-sm font-bold uppercase">Database is Empty</h3></div>
          ) : (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">

              {/* Power Consumption Trend */}
              <div className="bg-slate-900/60 p-6 rounded-2xl border border-slate-800 shadow-xl lg:col-span-2">
                <div className="flex items-center gap-2 mb-4 border-b border-slate-850 pb-2">
                  <h3 className="text-base font-bold text-slate-200">Power Consumption per Heat</h3>
                  <span className="ml-auto text-slate-500 text-xs font-bold uppercase">Energy Efficiency</span>
                </div>
                <div className="h-[300px] w-full mt-4">
                  <ResponsiveContainer width="100%" height="100%" minWidth={0} minHeight={0}>
                    <ComposedChart data={historicalData} margin={{ top: 20, right: 20, bottom: 20, left: 0 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                      <XAxis dataKey="meltNo" stroke="#475569" tick={{ fontSize: 10, fill: '#64748b' }} />
                      <YAxis stroke="#475569" tick={{ fontSize: 10, fill: '#64748b' }} />
                      <Tooltip content={<CustomTooltip />} />
                      <Legend wrapperStyle={{ fontSize: 11, paddingTop: 10 }} />
                      <Bar dataKey="powerUnits" name="Total Power Units" fill="#22d3ee" radius={[4, 4, 0, 0]} barSize={40} />
                      <Line type="monotone" dataKey="totalMetal" name="Metal Tapped (kg)" stroke="#818cf8" strokeWidth={3} dot={{ r: 4 }} />
                    </ComposedChart>
                  </ResponsiveContainer>
                </div>
              </div>

              {/* Tapping Temperature Stability */}
              <div className="bg-slate-900/60 p-6 rounded-2xl border border-slate-800 shadow-xl lg:col-span-2">
                <div className="flex items-center gap-2 mb-4 border-b border-slate-850 pb-2">
                  <h3 className="text-base font-bold text-slate-200">Tapping Temperature Stability</h3>
                  <span className="ml-auto text-slate-500 text-xs font-bold uppercase">Thermal Control</span>
                </div>
                <div className="h-[250px] w-full mt-4">
                  <ResponsiveContainer width="100%" height="100%" minWidth={0} minHeight={0}>
                    <LineChart data={historicalData} margin={{ top: 20, right: 20, bottom: 5, left: 0 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                      <XAxis dataKey="meltNo" stroke="#475569" tick={{ fontSize: 10, fill: '#64748b' }} />
                      <YAxis stroke="#475569" domain={['dataMin - 20', 'dataMax + 20']} tick={{ fontSize: 10, fill: '#64748b' }} />
                      <Tooltip content={<CustomTooltip />} />
                      <Legend wrapperStyle={{ fontSize: 11, paddingTop: 10 }} />
                      <ReferenceLine y={1640} label={{ value: "Target (1640°C)", fill: "#ef4444", fontSize: 10 }} stroke="#ef4444" strokeDasharray="4 4" />
                      <Line type="stepAfter" dataKey="tappingTemp" name="Furnace Tapping Temp (°C)" stroke="#fbbf24" strokeWidth={3} dot={{ r: 5, fill: '#f59e0b' }} />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </div>

            </div>
          )}
        </div>
      )}
    </div>
  );
}