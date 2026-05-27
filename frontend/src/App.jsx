import React from 'react';
import Dashboard from './pages/Dashboard';
import { Cpu, Layers, Activity } from 'lucide-react';

export default function App() {
    return (
        <div className="flex-1 flex flex-col min-h-screen bg-slate-900 text-slate-100 selection:bg-cyan-500 selection:text-slate-900">
            {/* Ambient Background Glows */}
            <div className="fixed inset-0 pointer-events-none overflow-hidden z-0">
                <div className="absolute top-[-10%] left-[-10%] w-[50%] h-[50%] rounded-full bg-cyan-500/10 blur-[120px]" />
                <div className="absolute bottom-[-10%] right-[-10%] w-[50%] h-[50%] rounded-full bg-indigo-500/10 blur-[120px]" />
            </div>

            {/* Premium Header */}
            <header className="sticky top-0 z-50 backdrop-blur-md bg-slate-900/80 border-b border-slate-800 shadow-lg shadow-slate-950/20">
                <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        <div className="p-2 rounded-xl bg-gradient-to-tr from-cyan-500 to-indigo-500 text-slate-950 shadow-md shadow-cyan-500/20">
                            <Cpu size={22} className="animate-pulse" />
                        </div>
                        <div>
                            <div className="flex items-center gap-2">
                                <h1 className="font-extrabold text-lg tracking-tight bg-gradient-to-r from-cyan-400 via-teal-300 to-indigo-400 bg-clip-text text-transparent">
                                    Intelligent Document Processor
                                </h1>
                                <span className="px-2 py-0.5 text-[10px] font-semibold tracking-wider text-cyan-400 bg-cyan-950/60 border border-cyan-800/50 rounded-full uppercase">
                                    v2.1
                                </span>
                            </div>
                            <p className="text-[10px] text-slate-400 font-medium tracking-wide">LADLE POURING & IDP VALIDATION SYSTEMS</p>
                        </div>
                    </div>

                    <div className="flex items-center gap-4 text-xs font-semibold text-slate-300">
                        <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800/80 border border-slate-700/60 shadow-inner">
                            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-ping" />
                            <span className="w-2 h-2 rounded-full bg-emerald-500 absolute" />
                            <span className="text-slate-400 ml-1">Engine:</span>
                            <span className="text-cyan-400">Vision Engine Active</span>
                        </div>
                    </div>
                </div>
            </header>

            {/* Main Content Area */}
            <main className="flex-1 z-10 relative">
                <Dashboard />
            </main>

            {/* Footer */}
            <footer className="z-10 py-6 border-t border-slate-800 bg-slate-950/40 text-center text-xs text-slate-500 font-medium">
                <div className="max-w-7xl mx-auto px-6 flex flex-col md:flex-row items-center justify-between gap-4">
                    <p>© 2026 Pouring Industry &bull; Advanced Metallurgy Intelligent System</p>
                    <div className="flex items-center gap-4 text-slate-400">
                        <span>Reliability Score: <strong className="text-cyan-400 font-semibold">99.8%</strong></span>
                        <span className="text-slate-600">|</span>
                        <span>Auto-Align Engine</span>
                    </div>
                </div>
            </footer>
        </div>
    );
}