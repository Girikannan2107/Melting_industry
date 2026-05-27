import React, { useState } from 'react';
import { 
  UploadCloud, 
  FileText, 
  CheckCircle, 
  AlertCircle, 
  Calendar, 
  Flame, 
  Thermometer, 
  Scale, 
  Layers, 
  Activity, 
  ArrowRight, 
  Clock, 
  Info,
  Layers3,
  Hash,
  Database
} from 'lucide-react';

export default function Dashboard() {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [dragActive, setDragActive] = useState(false);

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setError(null);
    }
  };

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
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
      const response = await fetch('http://localhost:8000/api/v1/documents/process', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`Server responded with status: ${response.status}`);
      }

      const data = await response.json();
      
      if (data.error) {
        throw new Error(data.error);
      }
      
      setResult(data.data);
    } catch (err) {
      setError(err.message || "Failed to process document.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-4 sm:p-8 space-y-8 max-w-[1600px] mx-auto z-10 relative">
      <style dangerouslySetInnerHTML={{__html: `
        .custom-scrollbar::-webkit-scrollbar {
          height: 10px;
        }
        .custom-scrollbar::-webkit-scrollbar-track {
          background: #0f172a;
          border-radius: 6px;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb {
          background: #334155;
          border-radius: 6px;
          border: 2px solid #0f172a;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb:hover {
          background: #475569;
        }
        @keyframes laser-scan {
          0%, 100% { top: 0%; opacity: 0.8; }
          50% { top: 100%; opacity: 0.3; }
        }
        .animate-laser {
          animation: laser-scan 3s ease-in-out infinite;
        }
      `}} />

      {/* Main Grid: Upload & File Status */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* Upload Panel */}
        <div className="lg:col-span-2 bg-slate-800/60 backdrop-blur-md p-6 rounded-2xl border border-slate-700/50 shadow-xl shadow-slate-950/20 flex flex-col justify-between">
          <div>
            <div className="flex items-center gap-3 mb-4">
              <Layers3 className="text-cyan-400" size={24} />
              <h2 className="text-xl font-bold text-slate-100">Intelligent Industrial Ingestor</h2>
            </div>
            <p className="text-slate-400 text-sm mb-6">
              Upload a handwritten or printed <strong>Ladle Pouring Record (PDF/JPG/PNG)</strong>. The system will leverage specialized AI OCR to semantically align and extract the document.
            </p>

            {/* Drag & Drop Zone */}
            <div 
              onDragEnter={handleDrag}
              onDragOver={handleDrag}
              onDragLeave={handleDrag}
              onDrop={handleDrop}
              className={`relative border-2 border-dashed rounded-xl p-8 flex flex-col items-center justify-center transition-all duration-300 ${
                dragActive ? 'border-cyan-400 bg-cyan-950/20 scale-[0.99]' : 'border-slate-600 bg-slate-900/40 hover:border-slate-500 hover:bg-slate-900/60'
              }`}
            >
              <input 
                id="file-upload"
                type="file" 
                onChange={handleFileChange}
                accept=".pdf,.jpg,.jpeg,.png"
                className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
              />
              <div className="p-4 bg-slate-800/80 rounded-full text-slate-400 mb-4 shadow-md">
                <UploadCloud size={32} className="text-cyan-400" />
              </div>
              <p className="text-slate-200 text-sm font-semibold mb-1">
                {file ? file.name : "Drag & Drop files here, or Click to Browse"}
              </p>
              <p className="text-slate-500 text-xs">
                Supports PDF, JPG, JPEG, PNG (Max 15MB)
              </p>

              {file && (
                <div className="mt-4 px-3 py-1.5 rounded-lg bg-cyan-950/40 border border-cyan-800/40 flex items-center gap-2 text-xs text-cyan-300">
                  <FileText size={14} />
                  <span>{(file.size / 1024).toFixed(1)} KB</span>
                </div>
              )}
            </div>
          </div>

          <div className="mt-6 flex items-center justify-end gap-4">
            <button 
              onClick={handleUpload}
              disabled={loading || !file}
              className={`w-full sm:w-auto px-8 py-3 rounded-xl font-semibold text-sm transition-all duration-300 flex items-center justify-center gap-2 shadow-lg ${
                loading || !file 
                  ? 'bg-slate-700 text-slate-500 cursor-not-allowed border border-slate-800' 
                  : 'bg-gradient-to-r from-cyan-500 to-indigo-500 hover:from-cyan-400 hover:to-indigo-400 text-slate-950 hover:scale-[1.02] shadow-cyan-500/10'
              }`}
            >
              {loading ? (
                <>
                  <span className="w-4 h-4 border-2 border-slate-950 border-t-transparent rounded-full animate-spin" />
                  <span>Processing Extraction...</span>
                </>
              ) : (
                <>
                  <span>Extract Structured Data</span>
                  <ArrowRight size={16} />
                </>
              )}
            </button>
          </div>
        </div>

        {/* Status / Processing Preview Panel */}
        <div className="bg-slate-800/60 backdrop-blur-md p-6 rounded-2xl border border-slate-700/50 shadow-xl shadow-slate-950/20 flex flex-col justify-between relative overflow-hidden">
          
          {/* Laser Line Overlay during Processing */}
          {loading && (
            <div className="absolute left-0 w-full h-1 bg-gradient-to-r from-transparent via-cyan-400 to-transparent shadow-[0_0_15px_#22d3ee] animate-laser z-20 pointer-events-none" />
          )}

          <div>
            <div className="flex items-center gap-3 mb-4">
              <Activity className="text-indigo-400" size={24} />
              <h2 className="text-xl font-bold text-slate-100">Engine Analytics</h2>
            </div>
            
            {loading ? (
              <div className="py-12 flex flex-col items-center justify-center text-center space-y-4">
                <div className="relative w-20 h-20">
                  <div className="absolute inset-0 rounded-full border-4 border-slate-700 border-t-cyan-400 animate-spin" />
                  <div className="absolute inset-2 rounded-full border-4 border-slate-700 border-t-indigo-400 animate-spin" style={{ animationDirection: 'reverse' }} />
                </div>
                <div>
                  <h3 className="text-slate-200 font-semibold">Neural OCR Vision Scanning</h3>
                  <p className="text-xs text-slate-400 mt-1 max-w-[250px]">
                    Performing pixel-level tabular segment mapping and handwriting correction...
                  </p>
                </div>
              </div>
            ) : result ? (
              <div className="space-y-4 py-2">
                <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-700/50 space-y-3">
                  <div className="flex items-center gap-2 text-slate-200 text-sm font-semibold border-b border-slate-800 pb-2">
                    <CheckCircle className="text-emerald-400" size={16} />
                    <span>Inference Succeeded</span>
                  </div>
                  <div className="grid grid-cols-2 gap-4 text-xs">
                    <div>
                      <span className="text-slate-500 block">Total Rows Extracted</span>
                      <strong className="text-slate-200 text-lg font-bold">
                        {result.table_data?.length || 0}
                      </strong>
                    </div>
                    <div>
                      <span className="text-slate-500 block">Identified Heat ID</span>
                      <strong className="text-cyan-400 text-sm font-bold truncate block">
                        {result.document_info?.heat_no || "N/A"}
                      </strong>
                    </div>
                  </div>
                </div>

                <div className="p-4 rounded-xl bg-slate-900/30 border border-slate-800/80 text-xs text-slate-400 space-y-2">
                  <div className="flex items-center gap-1.5 text-[11px] font-semibold text-slate-300">
                    <Info size={13} className="text-indigo-400" />
                    <span>AI Reasoning Notes</span>
                  </div>
                  <p>
                    Semantically aligned structural fields based on header positioning. Typographical errors in handwritten comments were cleaned up during OCR parse.
                  </p>
                </div>
              </div>
            ) : (
              <div className="py-12 flex flex-col items-center justify-center text-center text-slate-500">
                <Database size={40} className="stroke-[1.5] text-slate-600 mb-3" />
                <p className="text-sm">Ready for Document Upload</p>
                <p className="text-xs text-slate-600 max-w-[200px] mt-1">
                  Once uploaded, structured metrics and schema logs will display here.
                </p>
              </div>
            )}
          </div>

          {error && (
            <div className="mt-4 p-4 bg-rose-950/40 border border-rose-800/40 text-rose-300 rounded-xl flex gap-3 text-xs">
              <AlertCircle size={18} className="shrink-0 text-rose-400" />
              <div>
                <strong className="font-semibold block mb-0.5">Execution Failed</strong>
                <span>{error}</span>
              </div>
            </div>
          )}
        </div>

      </div>

      {/* Results Section */}
      {result && (
        <div className="space-y-8 animate-fade-in">
          
          {/* Metadata Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            
            {/* Document Info Card */}
            <div className="bg-gradient-to-br from-slate-800 to-slate-900/60 p-6 rounded-2xl border border-slate-700/50 shadow-lg relative overflow-hidden group">
              <div className="absolute top-0 right-0 p-6 opacity-5 group-hover:opacity-10 transition-opacity">
                <Calendar size={120} className="text-slate-100" />
              </div>
              <div className="flex items-center gap-3 mb-6">
                <div className="p-2 rounded-lg bg-cyan-950 text-cyan-400 border border-cyan-800/40">
                  <Calendar size={18} />
                </div>
                <h3 className="text-lg font-bold text-slate-100">Document Information</h3>
              </div>
              <div className="grid grid-cols-2 gap-6 text-sm">
                <div className="space-y-1">
                  <span className="text-slate-500 text-xs uppercase tracking-wider block font-semibold">Document Date</span>
                  <strong className="text-slate-200 text-base font-semibold">
                    {result.document_info?.date || 'N/A'}
                  </strong>
                </div>
                <div className="space-y-1">
                  <span className="text-slate-500 text-xs uppercase tracking-wider block font-semibold">Heat No / Batch</span>
                  <strong className="text-cyan-400 text-base font-semibold">
                    {result.document_info?.heat_no || 'N/A'}
                  </strong>
                </div>
                <div className="space-y-1 col-span-2">
                  <span className="text-slate-500 text-xs uppercase tracking-wider block font-semibold">Ladle Capacity / Specifications</span>
                  <strong className="text-slate-200 text-base font-semibold">
                    {result.document_info?.ladle_capacity || 'N/A'}
                  </strong>
                </div>
              </div>
            </div>
            
            {/* Pouring Details Card */}
            <div className="bg-gradient-to-br from-slate-800 to-slate-900/60 p-6 rounded-2xl border border-slate-700/50 shadow-lg relative overflow-hidden group">
              <div className="absolute top-0 right-0 p-6 opacity-5 group-hover:opacity-10 transition-opacity">
                <Flame size={120} className="text-slate-100" />
              </div>
              <div className="flex items-center gap-3 mb-6">
                <div className="p-2 rounded-lg bg-orange-950 text-orange-400 border border-orange-800/40">
                  <Flame size={18} />
                </div>
                <h3 className="text-lg font-bold text-slate-100">Ladle & Pouring Metrics</h3>
              </div>
              <div className="grid grid-cols-2 gap-6 text-sm">
                <div className="space-y-1">
                  <span className="text-slate-500 text-xs uppercase tracking-wider block font-semibold">Excess Metal Ingot</span>
                  <strong className="text-slate-200 text-base font-semibold flex items-baseline gap-1">
                    {result.pouring_details?.excess_metal_ingot_kg || 'N/A'}
                    <span className="text-xs text-slate-500 font-normal">kg</span>
                  </strong>
                </div>
                <div className="space-y-1">
                  <span className="text-slate-500 text-xs uppercase tracking-wider block font-semibold">Ladle Temperature</span>
                  <strong className="text-amber-400 text-base font-semibold flex items-center gap-1">
                    <Thermometer size={16} />
                    {result.pouring_details?.ladle_temperature || 'N/A'}
                  </strong>
                </div>
                <div className="space-y-1 col-span-2">
                  <span className="text-slate-500 text-xs uppercase tracking-wider block font-semibold">Pouring Temperatures (Sequence Logs)</span>
                  <div className="flex flex-wrap gap-2 mt-1">
                    {result.pouring_details?.pouring_temperatures && result.pouring_details.pouring_temperatures.length > 0 ? (
                      result.pouring_details.pouring_temperatures.map((temp, i) => (
                        <span key={i} className="px-2.5 py-1 rounded-md bg-amber-500/10 border border-amber-500/20 text-amber-400 text-xs font-semibold">
                          {temp}
                        </span>
                      ))
                    ) : (
                      <span className="text-slate-400 text-sm">N/A</span>
                    )}
                  </div>
                </div>
              </div>
            </div>

          </div>

          {/* Full 18-Column Extracted Grid */}
          <div className="bg-slate-800/60 backdrop-blur-md rounded-2xl border border-slate-700/50 shadow-xl overflow-hidden">
            
            <div className="p-6 border-b border-slate-700/60 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
              <div>
                <h3 className="text-lg font-bold text-slate-100 flex items-center gap-2">
                  <Scale size={20} className="text-cyan-400" />
                  <span>Complete Ladle Pouring Data Log (18 Columns)</span>
                </h3>
                <p className="text-slate-400 text-xs mt-1">
                  All handwritten columns have been mapped and fully reconciled under structural integrity validations.
                </p>
              </div>

              {/* Scroll Reminder */}
              <div className="px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 flex items-center gap-2 text-[11px] text-slate-400">
                <Info size={12} className="text-cyan-400" />
                <span>Swipe or Scroll horizontally to view all columns</span>
                <ArrowRight size={12} className="animate-bounce" />
              </div>
            </div>

            {/* Scrollable Container with Custom Webkit Scrollbars */}
            <div className="overflow-x-auto custom-scrollbar">
              <table className="min-w-full divide-y divide-slate-800 text-xs">
                
                {/* Headers */}
                <thead className="bg-slate-900/60 text-slate-400 uppercase font-semibold text-[10px] tracking-wider sticky top-0">
                  <tr>
                    <th scope="col" className="px-4 py-4 text-left border-r border-slate-800/40">#</th>
                    <th scope="col" className="px-4 py-4 text-left border-r border-slate-800/40 min-w-[90px]">Date</th>
                    <th scope="col" className="px-4 py-4 text-left border-r border-slate-800/40 min-w-[100px]">Heat No</th>
                    <th scope="col" className="px-4 py-4 text-left border-r border-slate-800/40 min-w-[220px]">Item Description</th>
                    <th scope="col" className="px-4 py-4 text-left border-r border-slate-800/40 min-w-[80px]">Grade</th>
                    <th scope="col" className="px-4 py-4 text-left border-r border-slate-800/40 min-w-[160px]">Customer</th>
                    <th scope="col" className="px-4 py-4 text-right border-r border-slate-800/40 min-w-[110px]">Planned Wt (Kg)</th>
                    <th scope="col" className="px-4 py-4 text-center border-r border-slate-800/40 min-w-[120px]">Planned Pour Time</th>
                    <th scope="col" className="px-4 py-4 text-left border-r border-slate-800/40 min-w-[260px]">Ladle Number & Size</th>
                    <th scope="col" className="px-4 py-4 text-center border-r border-slate-800/40 min-w-[100px]">Tapping Seq</th>
                    <th scope="col" className="px-4 py-4 text-center border-r border-slate-800/40 min-w-[100px]">Pouring Seq</th>
                    <th scope="col" className="px-4 py-4 text-center border-r border-slate-800/40 min-w-[120px]">Pour Time (sec)</th>
                    <th scope="col" className="px-4 py-4 text-right border-r border-slate-800/40 min-w-[140px]">Metal Before (Kg)</th>
                    <th scope="col" className="px-4 py-4 text-right border-r border-slate-800/40 min-w-[145px]">Metal After (Kg)</th>
                    <th scope="col" className="px-4 py-4 text-right border-r border-slate-800/40 min-w-[100px]">Kno Weight</th>
                    <th scope="col" className="px-4 py-4 text-right border-r border-slate-800/40 min-w-[125px]">Actual Liq (Kg)</th>
                    <th scope="col" className="px-4 py-4 text-right border-r border-slate-800/40 min-w-[110px]">Weight Diff</th>
                    <th scope="col" className="px-4 py-4 text-left border-r border-slate-800/40 min-w-[130px]">Remarks</th>
                    <th scope="col" className="px-4 py-4 text-right min-w-[140px]">Before Cutting Wt</th>
                  </tr>
                </thead>

                {/* Body Rows */}
                <tbody className="bg-slate-900/10 divide-y divide-slate-800/60 text-slate-300 font-medium">
                  {result.table_data && result.table_data.length > 0 ? (
                    result.table_data.map((row, index) => {
                      // Determine custom styling for values or rows if needed
                      const weightDiffNum = parseFloat(row.weight_diff);
                      const isNegativeDiff = row.weight_diff && row.weight_diff.toString().includes('-');
                      
                      return (
                        <tr key={index} className="hover:bg-slate-800/40 transition-colors">
                          <td className="px-4 py-3.5 text-slate-500 text-center font-bold border-r border-slate-800/40">
                            {index + 1}
                          </td>
                          <td className="px-4 py-3.5 whitespace-nowrap border-r border-slate-800/40 text-slate-400">
                            {row.date || <span className="text-slate-600">-</span>}
                          </td>
                          <td className="px-4 py-3.5 whitespace-nowrap border-r border-slate-800/40 font-semibold text-cyan-400">
                            {row.heat_no || <span className="text-slate-600">-</span>}
                          </td>
                          <td className="px-4 py-3.5 border-r border-slate-800/40 font-semibold text-slate-200">
                            {row.item || <span className="text-slate-600">-</span>}
                          </td>
                          <td className="px-4 py-3.5 border-r border-slate-800/40">
                            {row.grade ? (
                              <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-800 border border-slate-700 text-slate-300">
                                {row.grade}
                              </span>
                            ) : (
                              <span className="text-slate-600">-</span>
                            )}
                          </td>
                          <td className="px-4 py-3.5 border-r border-slate-800/40 text-slate-400">
                            {row.customer || <span className="text-slate-600">-</span>}
                          </td>
                          <td className="px-4 py-3.5 text-right border-r border-slate-800/40 font-mono text-slate-200">
                            {row.planned_pouring_weight || <span className="text-slate-600">-</span>}
                          </td>
                          <td className="px-4 py-3.5 text-center border-r border-slate-800/40 text-slate-400 font-mono">
                            {row.pouring_time_planned || <span className="text-slate-600">-</span>}
                          </td>
                          <td className="px-4 py-3.5 border-r border-slate-800/40 text-slate-400 text-[11px] truncate max-w-[260px]" title={row.ladle_number}>
                            {row.ladle_number || <span className="text-slate-600">-</span>}
                          </td>
                          <td className="px-4 py-3.5 text-center border-r border-slate-800/40 font-mono">
                            {row.tapping_sequence || <span className="text-slate-600">-</span>}
                          </td>
                          <td className="px-4 py-3.5 text-center border-r border-slate-800/40 font-mono">
                            {row.pouring_sequence || <span className="text-slate-600">-</span>}
                          </td>
                          <td className="px-4 py-3.5 text-center border-r border-slate-800/40 text-amber-400 font-mono">
                            {row.pouring_time_sec ? (
                              <span className="flex items-center justify-center gap-1">
                                <Clock size={12} className="opacity-60" />
                                {row.pouring_time_sec}
                              </span>
                            ) : (
                              <span className="text-slate-600">-</span>
                            )}
                          </td>
                          <td className="px-4 py-3.5 text-right border-r border-slate-800/40 font-mono text-slate-400">
                            {row.metal_weight_before_kg || <span className="text-slate-600">-</span>}
                          </td>
                          <td className="px-4 py-3.5 text-right border-r border-slate-800/40 font-mono text-slate-400">
                            {row.metal_weight_after_kg || <span className="text-slate-600">-</span>}
                          </td>
                          <td className="px-4 py-3.5 text-right border-r border-slate-800/40 font-mono text-slate-500">
                            {row.kno_weight || <span className="text-slate-600">-</span>}
                          </td>
                          <td className="px-4 py-3.5 text-right border-r border-slate-800/40 font-mono text-slate-200 font-semibold">
                            {row.actual_liquid_poured_kg || <span className="text-slate-600">-</span>}
                          </td>
                          <td className="px-4 py-3.5 text-right border-r border-slate-800/40 font-mono">
                            {row.weight_diff ? (
                              <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                                isNegativeDiff 
                                  ? 'bg-rose-500/10 border border-rose-500/20 text-rose-400' 
                                  : 'bg-emerald-500/10 border border-emerald-500/20 text-emerald-400'
                              }`}>
                                {row.weight_diff}
                              </span>
                            ) : (
                              <span className="text-slate-600">-</span>
                            )}
                          </td>
                          <td className="px-4 py-3.5 border-r border-slate-800/40 text-slate-400 italic">
                            {row.pouring_observation || <span className="text-slate-600">-</span>}
                          </td>
                          <td className="px-4 py-3.5 text-right font-mono text-cyan-400 font-bold bg-cyan-950/10">
                            {row.weight_before_cutting || <span className="text-slate-600">-</span>}
                          </td>
                        </tr>
                      );
                    })
                  ) : (
                    <tr>
                      <td colSpan="19" className="px-4 py-8 text-center text-slate-500 font-normal">
                        No table rows were processed or parsed.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>

            {/* Footer indicator summary */}
            <div className="bg-slate-900/60 p-4 border-t border-slate-700/60 flex items-center justify-between text-xs text-slate-500 font-medium">
              <span>Total rows processed: {result.table_data?.length || 0}</span>
              <span>Alignment Status: <strong className="text-cyan-400">Strict Mapping (18 columns)</strong></span>
            </div>

          </div>

        </div>
      )}

    </div>
  );
}