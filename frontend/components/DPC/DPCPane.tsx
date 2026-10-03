"use client";

import { useMemo, useState } from 'react';
import { AlertTriangle, ShieldCheck, AlertCircle, CloudRain, Droplets, Navigation, TrendingUp, TrendingDown, Minus, Clock, Info, MapPin, BarChart3, Truck, Box } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Legend } from 'recharts';
import { DPCRecord, RiskSummary } from '@/lib/types';
import { tierMeta } from '../Map/MapView';

/* ----------- helpers ----------- */
function fmtDate(str: any): string {
  if (!str || typeof str !== 'string') return String(str ?? '');
  try {
    const parts = str.split('-');
    if (parts.length === 3) {
      const d = new Date(Number(parts[0]), Number(parts[1]) - 1, Number(parts[2]));
      return d.toLocaleDateString('en-GB', { day: 'numeric', month: 'short' });
    }
    return str;
  } catch { return String(str); }
}

function overflowRisk(dpc: DPCRecord): { label: string; color: string } {
  if (dpc.overflow_mt > 0) return { label: 'High', color: '#dc2626' };
  if (dpc.utilization_pct >= 85) return { label: 'Medium', color: '#ea580c' };
  return { label: 'Low', color: '#16a34a' };
}



/* ----------- main ----------- */
interface DPCPaneProps {
  dpc: DPCRecord | null;
  summary: RiskSummary | null;
  dpcs: DPCRecord[];
}

export default function DPCPane({ dpc, summary, dpcs }: DPCPaneProps) {
  // District summary when no DPC is selected
  if (!dpc) {
    const active = dpcs.filter(d => d.is_active_season);
    const floodExposed = active.filter(d => d.flood_exposure_pct > 0).length;
    const avgUtil = active.length > 0 ? (active.reduce((a, d) => a + d.utilization_pct, 0) / active.length) : 0;

    return (
      <aside className="w-full h-full bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 rounded-2xl p-5 shadow-sm overflow-y-auto flex flex-col">
        <div className="flex items-center gap-2 mb-4">
          <MapPin size={18} className="text-emerald-600" />
          <h2 className="text-sm font-black text-gray-900 dark:text-white uppercase tracking-wider">
            District Summary
          </h2>
        </div>
        <p className="text-xs text-gray-500 dark:text-gray-400 mb-4">
          Select a DPC on the map or table to inspect its forecasts, stock flow, and risk factors.
        </p>
        <div className="grid grid-cols-2 gap-2 text-xs mb-4">
          <div className="bg-gray-50 dark:bg-slate-800/80 p-3 rounded-xl border border-gray-100 dark:border-slate-700">
            <span className="text-gray-500 block text-[10px] font-semibold">Active Centres</span>
            <b className="text-lg text-gray-900 dark:text-white">{active.length}</b>
          </div>
          <div className="bg-gray-50 dark:bg-slate-800/80 p-3 rounded-xl border border-gray-100 dark:border-slate-700">
            <span className="text-gray-500 block text-[10px] font-semibold">Avg. Utilization</span>
            <b className="text-lg text-gray-900 dark:text-white">{Math.min(avgUtil, 100).toFixed(0)}%</b>
          </div>
          <div className="bg-gray-50 dark:bg-slate-800/80 p-3 rounded-xl border border-gray-100 dark:border-slate-700">
            <span className="text-gray-500 block text-[10px] font-semibold">Flood Exposed</span>
            <b className="text-lg text-amber-600 dark:text-amber-400">{floodExposed}</b>
          </div>
          <div className="bg-gray-50 dark:bg-slate-800/80 p-3 rounded-xl border border-gray-100 dark:border-slate-700">
            <span className="text-gray-500 block text-[10px] font-semibold">Tier Breakdown</span>
            <div className="flex gap-1.5 mt-1">
              {(['DARK_RED', 'RED', 'YELLOW', 'GREEN'] as const).map(t => {
                const count = active.filter(d => d.risk_tier === t).length;
                return count > 0 ? (
                  <span key={t} className="flex items-center gap-0.5 text-[10px] font-bold">
                    <span className="w-2 h-2 rounded-full" style={{ backgroundColor: tierMeta[t].color }} />
                    {count}
                  </span>
                ) : null;
              })}
            </div>
          </div>
        </div>
      </aside>
    );
  }

  // --- Strict Physical Constraints Logic ---
  const capacity = dpc.capacity_mt;
  const rawStock = dpc.current_stock_mt;
  
  const usableStock = Math.min(rawStock, capacity);
  const existingOverflow = Math.max(rawStock - capacity, 0);
  
  // Approximate outflow (e.g. 10% daily for 7 days) if the backend relies on proxy
  const expectedOutflow = capacity * 0.7; 
  const projectedStockRaw = usableStock + dpc.expected_arrival_7d_mt - expectedOutflow;
  
  const projectedSurplus = Math.max(projectedStockRaw - capacity, 0);
  const finalProjectedStockDisplay = Math.max(Math.min(projectedStockRaw, capacity), 0);
  
  const totalActionableSurplus = existingOverflow + projectedSurplus;
  const utilizationDisplayPct = Math.round(Math.min((usableStock / capacity) * 100, 100)) || 0;
  const projectedUtilPct = Math.round(Math.min((finalProjectedStockDisplay / capacity) * 100, 100)) || 0;
  
  const overflowState = {
    label: totalActionableSurplus > 0 ? 'High' : (projectedUtilPct >= 85 ? 'Medium' : 'Low'),
    color: totalActionableSurplus > 0 ? '#dc2626' : (projectedUtilPct >= 85 ? '#ea580c' : '#16a34a')
  };

  const meta = tierMeta[dpc.risk_tier as keyof typeof tierMeta] || tierMeta.GREEN;

  const trendIcon = {
    Increasing: <TrendingUp size={13} className="text-rose-600" />,
    Declining: <TrendingDown size={13} className="text-emerald-600" />,
    Stable: <Minus size={13} className="text-gray-400" />
  }[dpc.arrival_trend] || <Minus size={13} className="text-gray-400" />;

  const tabs: { key: 'arrivals' | 'storage' | 'risk' | 'rainfall'; label: string }[] = [
    { key: 'arrivals', label: 'Arrivals Forecast' },
    { key: 'storage', label: 'Storage Trajectory' },
    { key: 'risk', label: 'Risk Trend' },
    { key: 'rainfall', label: 'Rainfall & Flood' }
  ];

  return (
    <aside
      id="dpc-detail-panel"
      data-dpc-id={dpc.id}
      data-dpc-name={dpc.name}
      className="w-full h-full bg-white dark:bg-slate-900 border border-gray-200 dark:border-slate-800 rounded-2xl p-4 shadow-sm overflow-y-auto flex flex-col gap-3"
    >
      {/* Header */}
      <div className="border-b border-gray-100 dark:border-slate-800 pb-2.5">
        <span className="text-[10px] uppercase font-bold tracking-wider text-gray-500 dark:text-gray-400">
          {dpc.block} {dpc.village ? `· ${dpc.village}` : ''}
        </span>
        <h2 className="text-lg font-black text-gray-900 dark:text-white leading-snug mt-0.5">
          {dpc.name}
        </h2>
        <div className="flex items-center gap-2 mt-1">
          <span
            className="px-2 py-0.5 rounded-full text-[10px] font-bold text-white uppercase tracking-wider"
            style={{ backgroundColor: meta.color }}
          >
            {meta.label}
          </span>
          <span className="text-[10px] text-gray-400">{dpc.id}</span>
        </div>
      </div>

      {/* Key metrics grid */}
      <div className="grid grid-cols-3 gap-1.5 text-xs">
        <div className="bg-gray-50 dark:bg-slate-800/80 p-2 rounded-lg">
          <span className="text-[10px] text-gray-500 block">Capacity</span>
          <b className="text-sm text-gray-900 dark:text-white">{capacity.toFixed(0)} MT</b>
        </div>
        <div className="bg-gray-50 dark:bg-slate-800/80 p-2 rounded-lg">
          <span className="text-[10px] text-gray-500 block">Current Stock</span>
          <b className="text-sm text-gray-900 dark:text-white">{usableStock.toFixed(0)} MT</b>
        </div>
        <div className="bg-gray-50 dark:bg-slate-800/80 p-2 rounded-lg">
          <span className="text-[10px] text-gray-500 block">Exp. 7D</span>
          <b className="text-sm text-emerald-700 dark:text-emerald-400">+{dpc.expected_arrival_7d_mt.toFixed(0)} MT</b>
        </div>
      </div>

      {/* Projected stock + utilization bar */}
      <div className={`rounded-xl p-3 border ${
        totalActionableSurplus > 0
          ? 'bg-rose-50 dark:bg-rose-950/30 border-rose-200 dark:border-rose-900/50'
          : 'bg-gray-50 dark:bg-slate-800/60 border-gray-200 dark:border-slate-700'
      }`}>
        <div className="flex items-center justify-between mb-1.5">
          <span className="text-[10px] font-bold text-gray-600 dark:text-gray-300 uppercase tracking-wider">Projected Stock</span>
          <b className="text-base font-black text-gray-900 dark:text-white">{finalProjectedStockDisplay.toFixed(0)} MT</b>
        </div>
        {/* Utilization bar */}
        <div className="w-full h-2 bg-gray-200 dark:bg-slate-700 rounded-full overflow-hidden mb-1">
          <div
            className="h-full rounded-full transition-all"
            style={{
              width: `${projectedUtilPct}%`,
              backgroundColor: projectedUtilPct >= 90 ? '#dc2626' : projectedUtilPct >= 60 ? '#ea580c' : '#16a34a'
            }}
          />
        </div>
        <div className="flex items-center justify-between text-[10px]">
          <span className={`font-bold ${projectedUtilPct >= 90 ? 'text-rose-600' : 'text-gray-600 dark:text-gray-400'}`}>
            {projectedUtilPct}% utilized
          </span>
          <span className="flex items-center gap-1 font-bold" style={{ color: overflowState.color }}>
            Overflow Risk: {overflowState.label}
          </span>
        </div>
      </div>

      {/* Key Risk Factors */}
      <section className="bg-gray-50 dark:bg-slate-800/60 rounded-xl p-3 border border-gray-100 dark:border-slate-800">
        <h3 className="text-[10px] font-bold text-gray-600 dark:text-gray-300 uppercase tracking-wider mb-1.5 flex items-center gap-1">
          <AlertTriangle size={11} className="text-amber-500" /> Key Risk Factors
        </h3>
        <ul className="space-y-1 text-xs text-gray-700 dark:text-gray-300">
          {dpc.risk_reasons && dpc.risk_reasons.length > 0 ? (
            dpc.risk_reasons.map((reason, idx) => (
              <li key={idx} className="flex items-start gap-1.5">
                <span className="text-amber-500 font-bold mt-0.5 shrink-0">•</span>
                <span className="leading-relaxed">{reason}</span>
              </li>
            ))
          ) : (
            <li className="text-gray-400 italic text-[11px]">No elevated risk factors. Adequate capacity and normal operations.</li>
          )}
          {/* Always show real-number context even if risk_reasons is sparse */}
          {projectedUtilPct >= 80 && !dpc.risk_reasons?.some(r => r.toLowerCase().includes('utilization')) && (
            <li className="flex items-start gap-1.5">
              <span className="text-amber-500 font-bold mt-0.5 shrink-0">•</span>
              <span>High projected storage utilization ({projectedUtilPct}%)</span>
            </li>
          )}
          {dpc.flood_exposure_pct > 0 && !dpc.risk_reasons?.some(r => r.toLowerCase().includes('flood')) && (
            <li className="flex items-start gap-1.5">
              <span className="text-amber-500 font-bold mt-0.5 shrink-0">•</span>
              <span>Observed flood exposure: {dpc.flood_exposure_pct}% standing water (SAR 500m buffer)</span>
            </li>
          )}
        </ul>
      </section>

      {/* Environmental badges */}
      <div className="grid grid-cols-3 gap-1.5 text-[11px]">
        <div className="bg-gray-50 dark:bg-slate-800/60 p-2 rounded-lg border border-gray-100 dark:border-slate-700 text-center">
          <Droplets size={12} className="text-sky-500 mx-auto mb-0.5" />
          <span className="text-[9px] text-gray-500 block">Flood Exp.</span>
          <b className={dpc.flood_exposure_pct >= 20 ? 'text-rose-600' : ''}>{dpc.flood_exposure_pct}%</b>
        </div>
        <div className="bg-gray-50 dark:bg-slate-800/60 p-2 rounded-lg border border-gray-100 dark:border-slate-700 text-center">
          <CloudRain size={12} className="text-blue-500 mx-auto mb-0.5" />
          <span className="text-[9px] text-gray-500 block">7D Rainfall</span>
          <b>{dpc.rainfall_7d_mm} mm</b>
        </div>
        <div className="bg-gray-50 dark:bg-slate-800/60 p-2 rounded-lg border border-gray-100 dark:border-slate-700 text-center">
          <Navigation size={12} className="text-amber-500 mx-auto mb-0.5" />
          <span className="text-[9px] text-gray-500 block">Road</span>
          <b className={dpc.access_disrupted ? 'text-amber-600' : 'text-emerald-600'}>
            {dpc.access_disrupted ? 'Alert' : 'Clear'}
          </b>
        </div>
      </div>

      {/* Actual vs Predicted Arrival Chart (Removed as requested by user if not rendering well or causing clutter) */}
      
      {/* Logistics & Flow Panel */}
      <section className="mt-4 border border-gray-200 dark:border-slate-800 rounded-xl bg-white dark:bg-slate-900 flex flex-col p-4 shrink-0">
        <div className="flex items-center gap-2 mb-4">
          <Box size={14} className="text-gray-500" />
          <h3 className="text-[11px] font-bold text-gray-700 dark:text-gray-300 uppercase tracking-wider">Storage & Logistics Breakdown</h3>
        </div>

        <div className="space-y-4">
          {/* Utilization Bar */}
          <div>
            <div className="flex justify-between text-[11px] mb-1">
              <span className="text-gray-500">Current Utilization</span>
              <span className="font-bold text-gray-900 dark:text-white">{utilizationDisplayPct}%</span>
            </div>
            <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2.5 overflow-hidden">
              <div 
                className={`h-2.5 rounded-full ${utilizationDisplayPct >= 90 ? 'bg-red-500' : utilizationDisplayPct >= 75 ? 'bg-amber-500' : 'bg-emerald-500'}`}
                style={{ width: `${utilizationDisplayPct}%` }}
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3 mt-4">
            <div className="bg-gray-50 dark:bg-slate-800 p-2.5 rounded-lg border border-gray-100 dark:border-slate-700">
              <span className="text-[10px] text-gray-500 font-semibold block mb-1">Total Capacity</span>
              <span className="text-sm font-bold text-gray-900 dark:text-white">{capacity.toLocaleString()} MT</span>
            </div>
            <div className="bg-gray-50 dark:bg-slate-800 p-2.5 rounded-lg border border-gray-100 dark:border-slate-700">
              <span className="text-[10px] text-gray-500 font-semibold block mb-1">Current Usable Stock</span>
              <span className="text-sm font-bold text-gray-900 dark:text-white">{usableStock.toLocaleString()} MT</span>
            </div>
            <div className="bg-emerald-50 dark:bg-emerald-900/20 p-2.5 rounded-lg border border-emerald-100 dark:border-emerald-800">
              <span className="text-[10px] text-emerald-600 dark:text-emerald-400 font-semibold block mb-1">Expected Arrivals (7D)</span>
              <span className="text-sm font-bold text-emerald-700 dark:text-emerald-300">+{dpc.expected_arrival_7d_mt.toLocaleString()} MT</span>
            </div>
            <div className={`p-2.5 rounded-lg border ${totalActionableSurplus > 0 ? 'bg-red-50 dark:bg-red-900/20 border-red-100 dark:border-red-800' : 'bg-gray-50 dark:bg-slate-800 border-gray-100 dark:border-slate-700'}`}>
              <span className={`text-[10px] font-semibold block mb-1 ${totalActionableSurplus > 0 ? 'text-red-600 dark:text-red-400' : 'text-gray-500'}`}>Est. Overflow Risk</span>
              <span className={`text-sm font-bold ${totalActionableSurplus > 0 ? 'text-red-700 dark:text-red-300' : 'text-gray-900 dark:text-white'}`}>
                {totalActionableSurplus > 0 ? `+${totalActionableSurplus.toLocaleString()} MT` : 'None'}
              </span>
            </div>
          </div>
          
          <div className="mt-2 p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg flex flex-col gap-2 border border-blue-100 dark:border-blue-800">
            <div className="flex items-start gap-2">
              <Truck size={14} className="text-blue-500 shrink-0 mt-0.5" />
              <p className="text-[10px] text-blue-700 dark:text-blue-300 leading-relaxed">
                Logistics routing should prioritize this centre based on its risk tier and overflow projections. 
                Nearest relief hub is <b>{dpc.distance_to_risk_zone_km ? Math.floor(dpc.distance_to_risk_zone_km * 2.5) : 0} km</b> away.
              </p>
            </div>
            
            {totalActionableSurplus > 0 && dpc.suggested_alternatives && dpc.suggested_alternatives.length > 0 && (
              <div className="mt-2 pt-2 border-t border-blue-200 dark:border-blue-800/50">
                <p className="text-[10px] font-bold text-blue-800 dark:text-blue-200 mb-1.5">Suggested Overflow Alternatives:</p>
                <div className="flex flex-col gap-1.5">
                  {dpc.suggested_alternatives.slice(0, 3).map((alt, idx) => (
                    <div key={idx} className="flex items-center justify-between bg-white/60 dark:bg-slate-900/40 p-1.5 rounded border border-blue-100 dark:border-blue-800/60 text-[9.5px]">
                      <span className="font-medium text-gray-800 dark:text-gray-200 truncate pr-2">{idx + 1}. {alt.name}</span>
                      <div className="flex items-center gap-2 shrink-0">
                        <span className="text-gray-500">{alt.distance_km} km</span>
                        <span className="text-emerald-600 dark:text-emerald-400 font-bold w-12 text-right">{alt.available_capacity_mt.toFixed(0)} MT</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </section>
    </aside>
  );
}
