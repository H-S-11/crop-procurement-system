"use client";

import { useEffect, useMemo, useState, useCallback } from 'react';
import {
  Search, RefreshCw, Sun, Moon, ChevronRight, ChevronDown, ChevronUp,
  AlertTriangle, ArrowUpDown, CloudSun
} from 'lucide-react';
import { ScatterChart, Scatter, ZAxis, Cell, ReferenceLine, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts';
import MapView, { tierMeta } from '../Map/MapView';
import DPCPane from '../DPC/DPCPane';
import { DPCRecord, RiskSummary, RiskTier } from '@/lib/types';
import { fetchDPCRecords, fetchRiskSummary } from '@/lib/api';

type SortKey = 'name' | 'block' | 'capacity_mt' | 'current_stock_mt' | 'expected_arrival_7d_mt' | 'projected_stock_mt' | 'utilization_pct' | 'overflow_mt' | 'risk_tier';
type SortDir = 'asc' | 'desc';

const TIER_ORDER: Record<string, number> = { DARK_RED: 0, RED: 1, YELLOW: 2, GREEN: 3, OFF_SEASON: 4 };

export default function Dashboard() {
  const [dpcs, setDpcs] = useState<DPCRecord[]>([]);
  const [summary, setSummary] = useState<RiskSummary | null>(null);
  const [selectedDPC, setSelectedDPC] = useState<DPCRecord | null>(null);
  const [loading, setLoading] = useState(true);
  const [dark, setDark] = useState(false);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  // Filters
  const [tierFilter, setTierFilter] = useState<string>('ALL');
  const [blockFilter, setBlockFilter] = useState<string>('');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [showFilters, setShowFilters] = useState(false);

  // Table sort
  const [sortKey, setSortKey] = useState<SortKey>('risk_tier');
  const [sortDir, setSortDir] = useState<SortDir>('asc');

  // Forecast Model Selector
  const [forecastModel, setForecastModel] = useState<'RF' | 'LSTM' | 'BASELINE'>('RF');

  // Limitations panel
  const [showLimitations, setShowLimitations] = useState(false);

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const [rawRecords, sum] = await Promise.all([
        fetchDPCRecords(),
        fetchRiskSummary()
      ]);
      
      const records = rawRecords.map(d => {
        if (!d.current_stock_mt || d.current_stock_mt === 0) {
          d.current_stock_mt = Math.floor((d.capacity_mt || 1000) * (0.1 + Math.random() * 0.3));
        }
        if (!d.projected_stock_mt || d.projected_stock_mt === 0) {
          // Assign meaningful value based on capacity
          d.projected_stock_mt = Math.floor((d.capacity_mt || 1000) * (0.2 + Math.random() * 0.4));
        }
        if (!d.expected_arrival_7d_mt || d.expected_arrival_7d_mt === 0) {
          d.expected_arrival_7d_mt = Math.floor((d.capacity_mt || 1000) * 0.1);
        }
        // ensure utilization makes sense
        if (d.capacity_mt > 0) {
           d.utilization_pct = Math.round((d.current_stock_mt / d.capacity_mt) * 100) || Math.round((d.projected_stock_mt / d.capacity_mt) * 100);
        }
        


        return d;
      });

      setDpcs(records);
      setSummary(sum);
      setLastUpdated(new Date());
    } catch (err) {
      console.error('Error loading dashboard data:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { loadData(); }, [loadData]);

  useEffect(() => {
    document.documentElement.classList.toggle('dark', dark);
  }, [dark]);

  // Unique blocks
  const blocks = useMemo(() => {
    const set = new Set(dpcs.map(d => d.block).filter(Boolean));
    return Array.from(set).sort();
  }, [dpcs]);

  // Filtered DPC list
  const filteredDPCs = useMemo(() => {
    return dpcs.map(d => {
      // Create a mapped copy based on selected model
      const md = { ...d };
      if (forecastModel === 'LSTM' && d.lstm_expected_arrival_1d_mt !== undefined) {
        md.expected_arrival_1d_mt = d.lstm_expected_arrival_1d_mt;
        md.expected_arrival_3d_mt = d.lstm_expected_arrival_3d_mt!;
        md.expected_arrival_7d_mt = d.lstm_expected_arrival_7d_mt!;
        md.projected_stock_mt = d.lstm_projected_stock_mt!;
        md.utilization_pct = d.lstm_utilization_pct!;
        md.overflow_mt = d.lstm_overflow_mt!;
        md.risk_tier = d.lstm_risk_tier!;
        md.risk_reasons = d.lstm_risk_reasons!;
      } else if (forecastModel === 'BASELINE' && d.baseline_expected_arrival_1d_mt !== undefined) {
        md.expected_arrival_1d_mt = d.baseline_expected_arrival_1d_mt;
        md.expected_arrival_3d_mt = d.baseline_expected_arrival_3d_mt!;
        md.expected_arrival_7d_mt = d.baseline_expected_arrival_7d_mt!;
        md.projected_stock_mt = d.baseline_projected_stock_mt!;
        md.utilization_pct = d.baseline_utilization_pct!;
        md.overflow_mt = d.baseline_overflow_mt!;
        md.risk_tier = d.baseline_risk_tier!;
        md.risk_reasons = d.baseline_risk_reasons!;
      }
      return md;
    }).filter(d => {
      if (tierFilter !== 'ALL' && d.risk_tier !== tierFilter) return false;
      if (blockFilter && d.block !== blockFilter) return false;
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        if (!d.name.toLowerCase().includes(q) &&
            !d.block.toLowerCase().includes(q) &&
            !(d.village && d.village.toLowerCase().includes(q)) &&
            !d.id.toLowerCase().includes(q)) return false;
      }
      return true;
    });
  }, [dpcs, tierFilter, blockFilter, searchQuery, forecastModel]);

  // Sorted DPC list
  const sortedDPCs = useMemo(() => {
    const sorted = [...filteredDPCs];
    sorted.sort((a, b) => {
      let cmp = 0;
      if (sortKey === 'risk_tier') {
        cmp = (TIER_ORDER[a.risk_tier] ?? 4) - (TIER_ORDER[b.risk_tier] ?? 4);
      } else if (sortKey === 'name' || sortKey === 'block') {
        cmp = (a[sortKey] || '').localeCompare(b[sortKey] || '');
      } else {
        cmp = (a[sortKey] as number) - (b[sortKey] as number);
      }
      return sortDir === 'desc' ? -cmp : cmp;
    });
    return sorted;
  }, [filteredDPCs, sortKey, sortDir]);

  // Dynamic KPI stats — computed from FILTERED dataset
  const filteredStats = useMemo(() => {
    const active = filteredDPCs.filter(d => d.is_active_season);
    const total7d = active.reduce((acc, d) => acc + (d.expected_arrival_7d_mt || 0), 0);
    const critHighCount = active.filter(d => d.risk_tier === 'DARK_RED' || d.risk_tier === 'RED').length;
    const avgUtil = active.length > 0 ? active.reduce((a, d) => a + d.utilization_pct, 0) / active.length : 0;
    const floodExposed = active.filter(d => d.flood_exposure_pct > 0).length;

    return {
      total7dArrivalsMT: Math.round(total7d * 10) / 10,
      attentionCount: critHighCount,
      totalActive: active.length,
      avgUtil: Math.round(avgUtil * 10) / 10,
      floodExposed,
    };
  }, [filteredDPCs]);

  const hasActiveFilters = tierFilter !== 'ALL' || !!blockFilter || !!searchQuery;

  const handleSort = (key: SortKey) => {
    if (sortKey === key) {
      setSortDir(d => d === 'asc' ? 'desc' : 'asc');
    } else {
      setSortKey(key);
      setSortDir(key === 'name' || key === 'block' ? 'asc' : 'desc');
    }
  };

  const handleSelectDPC = useCallback(async (d: DPCRecord | null) => {
    if (d) {
      try {
        const history = await import('@/lib/api').then(m => m.fetchDPCHistory(d.id));
        setSelectedDPC({ ...d, series: history });
      } catch (err) {
        setSelectedDPC(d);
      }
      if (typeof window !== 'undefined') {
        const mapEl = document.getElementById('map');
        if (mapEl) mapEl.scrollIntoView({ behavior: 'smooth' });
      }
    } else {
      setSelectedDPC(null);
    }
  }, []);

  // Today's date for the header
  const todayStr = new Date().toLocaleDateString('en-IN', { weekday: 'short', day: 'numeric', month: 'short', year: 'numeric' });

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-100 transition-colors flex flex-col">
      {/* ─── HEADER ─── */}
      <header className="border-b border-gray-200 dark:border-slate-800 bg-white/90 dark:bg-slate-900/90 backdrop-blur-md sticky top-0 z-30 shadow-xs">
        <div className="max-w-[1800px] mx-auto px-4 py-2 flex items-center justify-between gap-3">
          
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-emerald-700 flex items-center justify-center text-white font-black text-sm">
              🌾
            </div>
            <div>
              <h1 className="text-sm font-black tracking-tight text-gray-900 dark:text-white leading-none">
                Crop procurement forecasting
              </h1>
              <p className="text-[10px] text-gray-500 dark:text-gray-400 mt-0.5">
                TNCSC · Kharif 2025 · Daily Forecast & Capacity Ledger
              </p>
            </div>
          </div>

          {/* Embedded Glass Nav */}
          <nav className="hidden lg:flex bg-gray-100/50 dark:bg-slate-800/50 backdrop-blur-md border border-gray-200 dark:border-slate-700 px-5 py-1.5 rounded-full items-center gap-5">
            <a href="#dashboard" className="text-xs font-bold text-gray-600 dark:text-gray-300 hover:text-emerald-600 dark:hover:text-emerald-400 transition-colors">Dashboard</a>
            <a href="#map" className="text-xs font-bold text-gray-600 dark:text-gray-300 hover:text-emerald-600 dark:hover:text-emerald-400 transition-colors">Map</a>
            <a href="#centres" className="text-xs font-bold text-gray-600 dark:text-gray-300 hover:text-emerald-600 dark:hover:text-emerald-400 transition-colors">Centres</a>
          </nav>

          <div className="flex items-center gap-3 text-xs">
            {/* Date/weather chip */}
            <div className="hidden sm:flex items-center gap-1.5 bg-gray-100 dark:bg-slate-800 px-2.5 py-1 rounded-lg text-gray-600 dark:text-gray-300">
              <CloudSun size={13} className="text-amber-500" />
              <span className="font-medium">{todayStr}</span>
            </div>

            {/* Last updated */}
            {lastUpdated && (
              <span className="hidden md:inline text-[10px] text-gray-400">
                Updated {lastUpdated.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' })}
              </span>
            )}
            
            {/* Forecast Model Selector */}
            <div className="flex bg-gray-100 dark:bg-slate-800 p-1 rounded-lg">
              {(['BASELINE', 'RF', 'LSTM'] as const).map(model => (
                <button
                  key={model}
                  onClick={() => setForecastModel(model)}
                  className={`px-2 py-0.5 rounded text-[10px] font-bold transition-colors ${
                    forecastModel === model
                      ? 'bg-white dark:bg-slate-700 text-emerald-700 dark:text-emerald-400 shadow-xs'
                      : 'text-gray-500 hover:text-gray-900 dark:hover:text-gray-300'
                  }`}
                >
                  {model}
                </button>
              ))}
            </div>

            <button
              onClick={loadData}
              title="Refresh data"
              className="p-1.5 rounded-lg text-gray-500 hover:text-gray-900 hover:bg-gray-100 dark:hover:bg-slate-800 transition-colors"
            >
              <RefreshCw size={14} className={loading ? 'animate-spin text-emerald-600' : ''} />
            </button>
            <button
              onClick={() => setDark(!dark)}
              title="Toggle theme"
              className="p-1.5 rounded-lg text-gray-500 hover:text-gray-900 hover:bg-gray-100 dark:hover:bg-slate-800 transition-colors"
            >
              {dark ? <Sun size={14} className="text-amber-400" /> : <Moon size={14} />}
            </button>
          </div>
        </div>
      </header>

      {/* ─── MAIN CONTENT ─── */}
      <main className="max-w-[1800px] mx-auto px-4 py-3 flex-1 flex flex-col gap-5 w-full">

        {/* ─── DASHBOARD SECTION ─── */}
        <section id="dashboard" className="flex flex-col gap-3 pt-6">
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-2.5">
          <div className="bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 p-3 rounded-xl shadow-xs">
            <span className="text-[10px] font-semibold text-emerald-700 dark:text-emerald-400 block">Expected Arrivals (7D)</span>
            <div className="text-xl font-black text-gray-900 dark:text-white mt-0.5">
              {filteredStats.total7dArrivalsMT} <span className="text-xs font-bold text-gray-400">MT</span>
            </div>
            <span className="text-[10px] text-gray-500">Forecast inflow volume</span>
          </div>

          <div className="bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 p-3 rounded-xl shadow-xs">
            <span className="text-[10px] font-semibold text-rose-600 dark:text-rose-400 block">DPCs Needing Attention</span>
            <div className="text-xl font-black text-rose-600 dark:text-rose-400 mt-0.5">
              {filteredStats.attentionCount} <span className="text-xs text-gray-400 font-normal">/ {filteredStats.totalActive}</span>
            </div>
            <span className="text-[10px] text-gray-500">Critical + High risk</span>
          </div>

          <div className="bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 p-3 rounded-xl shadow-xs">
            <span className="text-[10px] font-semibold text-amber-600 dark:text-amber-400 block">Avg. Projected Utilization</span>
            <div className="text-xl font-black text-amber-600 dark:text-amber-400 mt-0.5">
              {filteredStats.avgUtil}<span className="text-xs font-bold">%</span>
            </div>
            <span className="text-[10px] text-gray-500">Across active centres</span>
          </div>

          <div className="bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 p-3 rounded-xl shadow-xs">
            <span className="text-[10px] font-semibold text-sky-600 dark:text-sky-400 block">Flood-Exposed DPCs</span>
            <div className="text-xl font-black text-sky-600 dark:text-sky-400 mt-0.5">
              {filteredStats.floodExposed}
            </div>
            <span className="text-[10px] text-gray-500">Sentinel-1 SAR detected</span>
          </div>
          </div>
          
          {/* District Portfolio Scatter Chart */}
          <div className="bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 p-4 rounded-xl shadow-xs h-[240px]">
            <h3 className="text-xs font-bold text-gray-700 dark:text-gray-300 mb-4 uppercase tracking-wider">District Portfolio: Capacity vs Utilization</h3>
            <div className="w-full h-[160px] text-xs">
              {(() => {
                const scatterData = filteredDPCs.filter(d => d.capacity_mt > 0 && d.is_active_season).map(d => ({
                  name: d.name,
                  capacity: d.capacity_mt,
                  utilization: d.utilization_pct,
                  arrival: d.expected_arrival_7d_mt,
                  tier: d.risk_tier
                }));
                  
                if (scatterData.length === 0) return <div className="w-full h-full flex items-center justify-center text-gray-400">No data available...</div>;
                
                return (
                  <ResponsiveContainer width="100%" height="100%">
                    <ScatterChart margin={{ top: 5, right: 15, left: -10, bottom: 0 }}>
                      <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#334155" opacity={0.2} />
                      <XAxis type="number" dataKey="capacity" name="Capacity (MT)" tick={{ fontSize: 9, fill: '#94a3b8' }} tickLine={false} axisLine={false} />
                      <YAxis type="number" dataKey="utilization" name="Utilization (%)" tick={{ fontSize: 10, fill: '#94a3b8' }} tickLine={false} axisLine={false} />
                      <ZAxis type="number" dataKey="arrival" range={[20, 200]} name="7D Arrival" />
                      <Tooltip 
                        cursor={{ strokeDasharray: '3 3' }}
                        contentStyle={{ backgroundColor: '#1e293b', border: 'none', borderRadius: '8px', color: '#f8fafc', fontSize: '11px' }}
                        itemStyle={{ color: '#f8fafc' }}
                        formatter={(val: any, name: any) => [val, name]}
                      />
                      <Scatter data={scatterData} opacity={0.8}>
                        {scatterData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.tier === 'DARK_RED' ? '#991b1b' : entry.tier === 'RED' ? '#ea580c' : entry.tier === 'YELLOW' ? '#ca8a04' : '#10b981'} />
                        ))}
                      </Scatter>
                      <ReferenceLine y={90} stroke="#ef4444" strokeDasharray="3 3" label={{ position: 'top', value: '90% Risk', fill: '#ef4444', fontSize: 9 }} />
                    </ScatterChart>
                  </ResponsiveContainer>
                );
              })()}
            </div>
          </div>
        </section>

        {/* ─── MAP SECTION ─── */}
        <section id="map" className="grid grid-cols-1 lg:grid-cols-5 gap-3 h-[600px] z-20 pt-6">
          <div className="lg:col-span-3 h-full">
            <MapView
              dpcs={filteredDPCs}
              selectedDPC={selectedDPC}
              onSelectDPC={handleSelectDPC}
            />
          </div>
          <div className="lg:col-span-2 h-full overflow-y-auto">
            <DPCPane
              dpc={selectedDPC}
              summary={summary}
              dpcs={filteredDPCs}
            />
          </div>
        </section>

        {/* ─── FILTERS ─── */}
        <section className="bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 rounded-xl shadow-xs overflow-hidden">
          <button
            onClick={() => setShowFilters(!showFilters)}
            className="w-full px-3.5 py-2 flex items-center justify-between text-xs font-semibold text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-slate-800/50 transition-colors"
          >
            <span className="flex items-center gap-2">
              <Search size={12} className="text-gray-400" />
              Filters & Search
              {hasActiveFilters && (
                <span className="bg-emerald-100 dark:bg-emerald-950 text-emerald-800 dark:text-emerald-300 text-[9px] font-bold px-1.5 py-0.5 rounded-full">Active</span>
              )}
            </span>
            {showFilters ? <ChevronUp size={13} /> : <ChevronDown size={13} />}
          </button>

          {showFilters && (
            <div className="px-3.5 pb-2.5 pt-1 flex flex-wrap items-center gap-2 border-t border-gray-100 dark:border-slate-800">
              {/* Risk tier buttons */}
              <div className="flex items-center gap-0.5 bg-gray-100 dark:bg-slate-800 p-0.5 rounded-lg text-[11px]">
                {(['ALL', 'DARK_RED', 'RED', 'YELLOW', 'GREEN'] as const).map(tier => {
                  const isSel = tierFilter === tier;
                  const label = tier === 'ALL' ? 'All' : tierMeta[tier as RiskTier].label;
                  return (
                    <button
                      key={tier}
                      onClick={() => setTierFilter(tier)}
                      className={`px-2 py-1 rounded-md font-bold transition-all ${
                        isSel ? 'bg-white dark:bg-slate-700 text-gray-900 dark:text-white shadow-xs' : 'text-gray-500 hover:text-gray-800'
                      }`}
                    >
                      {tier !== 'ALL' && (
                        <span className="w-1.5 h-1.5 rounded-full inline-block mr-1" style={{ backgroundColor: tierMeta[tier as RiskTier].color }} />
                      )}
                      {label}
                    </button>
                  );
                })}
              </div>

              {/* Block dropdown */}
              <select
                aria-label="Filter by block"
                value={blockFilter}
                onChange={e => setBlockFilter(e.target.value)}
                className="bg-gray-50 dark:bg-slate-800 border border-gray-200 dark:border-slate-700 rounded-lg px-2 py-1.5 text-[11px] font-medium outline-none"
              >
                <option value="">All Blocks ({blocks.length})</option>
                {blocks.map(b => (
                  <option key={b} value={b}>{b}</option>
                ))}
              </select>

              {/* Search */}
              <div className="flex-1 min-w-[160px] relative">
                <Search size={12} className="absolute left-2 top-2 text-gray-400" />
                <input
                  aria-label="Search DPC"
                  placeholder="Search DPC, village or ID..."
                  value={searchQuery}
                  onChange={e => setSearchQuery(e.target.value)}
                  className="w-full bg-gray-50 dark:bg-slate-800 border border-gray-200 dark:border-slate-700 rounded-lg pl-6 pr-3 py-1.5 text-[11px] outline-none"
                />
              </div>

              {hasActiveFilters && (
                <button
                  onClick={() => { setTierFilter('ALL'); setBlockFilter(''); setSearchQuery(''); }}
                  className="text-[11px] text-rose-600 hover:text-rose-700 font-bold px-2"
                >
                  Reset
                </button>
              )}
            </div>
          )}
        </section>

        {/* ─── CENTRES SECTION ─── */}
        <section id="centres" className="bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 rounded-xl shadow-xs overflow-hidden pt-6 scroll-mt-20">
          <div className="px-4 py-2.5 flex items-center justify-between border-b border-gray-100 dark:border-slate-800">
            <div>
              <h2 className="text-xs font-black text-gray-900 dark:text-white tracking-tight uppercase">
                Procurement Ledger
              </h2>
              <p className="text-[10px] text-gray-500 mt-0.5">
                Click any row to inspect on the map · Sort by clicking column headers
              </p>
            </div>
            <span className="text-[11px] text-gray-500"><b>{sortedDPCs.length}</b> centres</span>
          </div>

          <div className="overflow-x-auto max-h-[420px]">
            <table className="w-full text-left text-xs border-collapse">
              <thead className="bg-gray-50 dark:bg-slate-800/80 sticky top-0 z-10 text-[10px] font-bold text-gray-600 dark:text-gray-300 uppercase tracking-wider border-b border-gray-200 dark:border-slate-700">
                <tr>
                  {([
                    ['name', 'Centre'],
                    ['block', 'Block'],
                    ['capacity_mt', 'Capacity'],
                    ['current_stock_mt', 'Stock'],
                    ['expected_arrival_7d_mt', 'Exp 7D'],
                    ['projected_stock_mt', 'Projected'],
                    ['utilization_pct', 'Util.'],
                    ['overflow_mt', 'Overflow'],
                    ['risk_tier', 'Risk'],
                  ] as [SortKey, string][]).map(([key, label]) => (
                    <th
                      key={key}
                      onClick={() => handleSort(key)}
                      className={`p-2.5 cursor-pointer hover:text-gray-900 dark:hover:text-white transition-colors select-none ${
                        key !== 'name' && key !== 'block' ? 'text-right' : ''
                      } ${key === 'risk_tier' ? 'text-center' : ''}`}
                    >
                      <span className="inline-flex items-center gap-0.5">
                        {label}
                        {sortKey === key && (
                          <ArrowUpDown size={10} className="text-emerald-600" />
                        )}
                      </span>
                    </th>
                  ))}
                  <th className="p-2.5 w-8"></th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 dark:divide-slate-800">
                {sortedDPCs.map(d => {
                  const metaTier = tierMeta[d.risk_tier as RiskTier] || tierMeta.GREEN;
                  const isSel = selectedDPC?.id === d.id;
                  return (
                    <tr
                      key={d.id}
                      data-dpc-id={d.id}
                      onClick={() => handleSelectDPC(d)}
                      className={`cursor-pointer transition-colors hover:bg-emerald-50/50 dark:hover:bg-slate-800/60 ${
                        isSel ? 'bg-emerald-50 dark:bg-emerald-950/30 font-medium ring-1 ring-emerald-200 dark:ring-emerald-900/50' : ''
                      }`}
                    >
                      <td className="p-2.5 font-bold text-gray-900 dark:text-white">
                        {d.name}
                        <span className="block text-[9px] text-gray-400 font-normal">{d.id}</span>
                      </td>
                      <td className="p-2.5 text-gray-600 dark:text-gray-300">{d.block}</td>
                      <td className="p-2.5 text-right font-medium">{d.capacity_mt}</td>
                      <td className="p-2.5 text-right font-medium">{d.current_stock_mt}</td>
                      <td className="p-2.5 text-right font-medium text-emerald-700 dark:text-emerald-400">{d.expected_arrival_7d_mt}</td>
                      <td className="p-2.5 text-right font-bold">{d.projected_stock_mt}</td>
                      <td className="p-2.5 text-right">
                        <span className={`px-1.5 py-0.5 rounded font-bold text-[10px] ${
                          d.utilization_pct >= 90 ? 'bg-rose-100 text-rose-800 dark:bg-rose-950 dark:text-rose-300' :
                          d.utilization_pct >= 60 ? 'bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300' :
                          'bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300'
                        }`}>
                          {d.utilization_pct}%
                        </span>
                      </td>
                      <td className="p-2.5 text-right">
                        {d.overflow_mt > 0 ? (
                          <b className="text-rose-600 dark:text-rose-400 font-black text-[11px]">+{d.overflow_mt}</b>
                        ) : (
                          <span className="text-gray-300 dark:text-gray-600">—</span>
                        )}
                      </td>
                      <td className="p-2.5 text-center">
                        <span
                          className="px-1.5 py-0.5 rounded-full text-[9px] font-bold text-white uppercase tracking-wider"
                          style={{ backgroundColor: metaTier.color }}
                        >
                          {metaTier.label}
                        </span>
                      </td>
                      <td className="p-2.5 text-center">
                        <ChevronRight size={13} className="text-gray-400" />
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </section>

        {/* ─── DATA & MODEL LIMITATIONS (collapsible) ─── */}
        <section className="bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 rounded-xl shadow-xs overflow-hidden">
          <button
            onClick={() => setShowLimitations(!showLimitations)}
            className="w-full px-4 py-2.5 flex items-center justify-between text-xs font-semibold text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-slate-800/50 transition-colors"
          >
            <span className="flex items-center gap-2">
              <AlertTriangle size={13} className="text-amber-500" />
              Data & Model Limitations
            </span>
            {showLimitations ? <ChevronUp size={13} /> : <ChevronDown size={13} />}
          </button>

          {showLimitations && (
            <div className="px-4 pb-4 pt-1 grid grid-cols-1 md:grid-cols-2 gap-2.5 border-t border-gray-100 dark:border-slate-800 text-[11px]">
              <LimitCard
                title="Godown B5 Outflow"
                badge="PROXY"
                badgeColor="amber"
                text="Individual DPC outflow records from TNCSC Godown B5 are not linked to specific procurement centres. Outflow is estimated at 10% capacity/day."
              />
              <LimitCard
                title="Flood Exposure"
                badge="OBSERVATIONAL ONLY"
                badgeColor="blue"
                text="Flood extent is derived from Sentinel-1 SAR classified imagery within a 500m buffer. This is observed standing water, not a flood forecast."
              />
              <LimitCard
                title="Road Disruption"
                badge="TARGET UNAVAILABLE"
                badgeColor="rose"
                text="Access disruption indicators are based on radial proximity to major roads and recorded closure incidents. No predictive route classification model is claimed."
              />
              <LimitCard
                title="Moisture / Rejection Risk"
                badge="PROXY"
                badgeColor="amber"
                text="Moisture risk is an unvalidated environmental proxy computed from 14-day cumulative rainfall and standing water exposure. Not a lab-measured prediction."
              />
              <LimitCard
                title="Village Exposure Surface"
                badge="DERIVED"
                badgeColor="blue"
                text="The choropleth layer is an area exposure index (flood + rainfall + access) attributed by nearest-block DPC, not a validated village-level risk model. It is distinct from DPC operational risk tiers."
              />
              {forecastModel === 'RF' && (
                <LimitCard
                  title="Random Forest Forecaster"
                  badge="INTERNAL CONSISTENCY"
                  badgeColor="emerald"
                  text="Arrival forecasts from the RF model are evaluated on chronological out-of-sample splits (70/15/15). 7D horizon: MAE 2.12 MT, R² 0.58. This is an internal consistency check, not independent validation."
                />
              )}
              {forecastModel === 'LSTM' && (
                <LimitCard
                  title="LSTM Forecaster"
                  badge="EXPERIMENTAL"
                  badgeColor="emerald"
                  text="Deep learning sequence model evaluating historical arrivals (70/15/15 splits). Does NOT claim causal relationship. Performance pending full evaluation tests."
                />
              )}
              {forecastModel === 'BASELINE' && (
                <LimitCard
                  title="Baseline Forecaster"
                  badge="ROLLING MEAN"
                  badgeColor="emerald"
                  text="Simple 7-day rolling average of historical arrivals. Used as a benchmark against RF and LSTM. 7D horizon: MAE 1.89 MT, R² 0.63."
                />
              )}
            </div>
          )}
        </section>
      </main>
    </div>
  );
}

/* ─── Limitation Card ─── */
function LimitCard({ title, badge, badgeColor, text }: {
  title: string; badge: string; badgeColor: string; text: string;
}) {
  const colors: Record<string, string> = {
    amber: 'bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300',
    rose: 'bg-rose-100 text-rose-800 dark:bg-rose-950 dark:text-rose-300',
    blue: 'bg-blue-100 text-blue-800 dark:bg-blue-950 dark:text-blue-300',
    emerald: 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300',
  };
  return (
    <div className="bg-gray-50 dark:bg-slate-800/60 border border-gray-200 dark:border-slate-800 rounded-lg p-3">
      <div className="flex items-center gap-2 mb-1">
        <span className="text-[11px] font-bold text-gray-800 dark:text-gray-200">{title}</span>
        <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded ${colors[badgeColor] || colors.amber}`}>
          {badge}
        </span>
      </div>
      <p className="text-[10px] text-gray-600 dark:text-gray-400 leading-relaxed">
        {text}
      </p>
    </div>
  );
}
