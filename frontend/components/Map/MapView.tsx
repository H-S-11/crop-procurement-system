"use client";

import { useMemo, useRef, useState, useEffect, useCallback } from 'react';
import type { Map as MapLibreMap } from 'maplibre-gl';
import Map, { Layer, Source, NavigationControl, Popup, Marker, type MapRef } from 'react-map-gl/maplibre';
import { DPCRecord, RiskTier } from '@/lib/types';
import { Layers, Eye, EyeOff } from 'lucide-react';

const THANJAVUR_CENTER: [number, number] = [79.18, 10.75];
const DISTRICT_ZOOM = 9;
const THANJAVUR_BOUNDS: [number, number, number, number] = [78.75, 10.10, 79.62, 11.22];

const positron = 'https://basemaps.cartocdn.com/gl/positron-gl-style/style.json';
const osmFallback: any = {
  version: 8,
  sources: {
    osm: {
      type: 'raster',
      tiles: ['https://tile.openstreetmap.org/{z}/{x}/{y}.png'],
      tileSize: 256,
      attribution: '© OpenStreetMap contributors'
    }
  },
  layers: [{ id: 'osm', type: 'raster', source: 'osm' }]
};

const satelliteStyle: any = {
  version: 8,
  sources: {
    satellite: {
      type: 'raster',
      tiles: ['https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}'],
      tileSize: 256,
      attribution: '© Esri'
    }
  },
  layers: [{ id: 'satellite', type: 'raster', source: 'satellite' }]
};

export const tierMeta: Record<RiskTier, { label: string; icon: string; color: string; desc: string }> = {
  DARK_RED: { label: 'Critical', icon: '⬣', color: '#991b1b', desc: 'Multiple severe factors / Overflow' },
  RED: { label: 'High Attention', icon: '▲', color: '#ea580c', desc: 'Near capacity / Flood / Surge' },
  YELLOW: { label: 'Monitor', icon: '!', color: '#ca8a04', desc: 'Moderate utilization / Rain' },
  GREEN: { label: 'Normal', icon: '✓', color: '#16a34a', desc: 'Adequate capacity & clear access' },
  OFF_SEASON: { label: 'Normal', icon: '✓', color: '#16a34a', desc: 'Inactive in current harvest' }
};

interface MapViewProps {
  dpcs: DPCRecord[];
  selectedDPC: DPCRecord | null;
  onSelectDPC: (d: DPCRecord | null) => void;
}

export default function MapView({ dpcs, selectedDPC, onSelectDPC }: MapViewProps) {
  const mapRef = useRef<MapRef>(null);
  const [hoveredDPC, setHoveredDPC] = useState<DPCRecord | null>(null);
  const [useFallbackStyle, setUseFallbackStyle] = useState(false);
  
  // Modes: 'default' | 'satellite' | 'risk'
  const [mapMode, setMapMode] = useState<'default' | 'satellite' | 'risk'>('default');
  
  const pulseTimerRef = useRef<number | null>(null);
  const [pulsePhase, setPulsePhase] = useState(0);

  // Pulse animation for selected marker
  useEffect(() => {
    if (selectedDPC) {
      const interval = window.setInterval(() => {
        setPulsePhase(p => (p + 1) % 60);
      }, 50);
      pulseTimerRef.current = interval;
      return () => window.clearInterval(interval);
    } else {
      setPulsePhase(0);
    }
  }, [selectedDPC?.id]);

  // DPC GeoJSON
  const dpcGeojson = useMemo(() => ({
    type: 'FeatureCollection' as const,
    features: dpcs
      .filter(d => d.lon != null && d.lat != null && !isNaN(Number(d.lon)) && !isNaN(Number(d.lat)))
      .map(d => ({
        type: 'Feature' as const,
        geometry: { type: 'Point' as const, coordinates: [Number(d.lon), Number(d.lat)] },
        properties: {
          id: d.id,
          name: d.name,
          block: d.block,
          risk_tier: d.risk_tier,
          utilization_pct: d.utilization_pct,
          overflow_mt: d.overflow_mt,
          expected_arrival_7d_mt: d.expected_arrival_7d_mt,
          is_selected: selectedDPC?.id === d.id ? 1 : 0
        }
      }))
  }), [dpcs, selectedDPC?.id]);

  // Selected DPC highlight ring GeoJSON
  const selectedGeojson = useMemo(() => {
    if (!selectedDPC) return { type: 'FeatureCollection' as const, features: [] };
    const radius = 14 + Math.sin(pulsePhase * 0.21) * 4;
    return {
      type: 'FeatureCollection' as const,
      features: [{
        type: 'Feature' as const,
        geometry: { type: 'Point' as const, coordinates: [Number(selectedDPC.lon), Number(selectedDPC.lat)] },
        properties: { radius }
      }]
    };
  }, [selectedDPC, pulsePhase]);

  // Relief Lines GeoJSON
  const reliefLinesGeojson = useMemo(() => {
    if (!selectedDPC || !selectedDPC.suggested_alternatives || selectedDPC.suggested_alternatives.length === 0) {
      return { type: 'FeatureCollection' as const, features: [] };
    }
    
    // Strict physical constraints check - only draw if there is an actual overflow
    const projectedSurplus = Math.max((selectedDPC.projected_stock_mt || 0) - (selectedDPC.capacity_mt || 0), 0);
    if (projectedSurplus <= 0) return { type: 'FeatureCollection' as const, features: [] };

    const features = selectedDPC.suggested_alternatives.map(alt => {
      const altDpc = dpcs.find(d => d.id === alt.id);
      if (!altDpc || altDpc.lon == null || altDpc.lat == null) return null;
      return {
        type: 'Feature' as const,
        geometry: {
          type: 'LineString' as const,
          coordinates: [
            [Number(selectedDPC.lon), Number(selectedDPC.lat)],
            [Number(altDpc.lon), Number(altDpc.lat)]
          ]
        },
        properties: {
          distance: alt.distance_km,
          name: alt.name
        }
      };
    }).filter(Boolean);
    
    return { type: 'FeatureCollection' as const, features };
  }, [selectedDPC, dpcs]);

  const onMapReady = useCallback((event: any) => {
    const map = event.target as MapLibreMap;
    map.fitBounds(
      [[THANJAVUR_BOUNDS[0], THANJAVUR_BOUNDS[1]], [THANJAVUR_BOUNDS[2], THANJAVUR_BOUNDS[3]]],
      { padding: 24, duration: 0 }
    );
  }, []);

  const handleClick = useCallback((e: any) => {
    const feat = e.features?.[0];
    if (feat?.properties?.id) {
      const found = dpcs.find(d => d.id === feat.properties.id);
      if (found) {
        onSelectDPC(found);
        return;
      }
    }
    // Click on empty space: deselect, reset to district view
    onSelectDPC(null);
  }, [dpcs, onSelectDPC]);

  const handleMouseMove = useCallback((e: any) => {
    const feat = e.features?.[0];
    if (feat?.properties?.id) {
      const found = dpcs.find(d => d.id === feat.properties.id);
      setHoveredDPC(found || null);
      if (mapRef.current) {
        (mapRef.current.getMap() as any).getCanvas().style.cursor = 'pointer';
      }
    } else {
      setHoveredDPC(null);
      if (mapRef.current) {
        (mapRef.current.getMap() as any).getCanvas().style.cursor = '';
      }
    }
  }, [dpcs]);

  // FlyTo on selection
  useEffect(() => {
    if (!mapRef.current) return;
    if (selectedDPC) {
      mapRef.current.flyTo({
        center: [selectedDPC.lon, selectedDPC.lat],
        zoom: 12.5,
        duration: 1200,
        essential: true
      });
    } else {
      // Reset to district view
      mapRef.current.flyTo({
        center: THANJAVUR_CENTER,
        zoom: DISTRICT_ZOOM,
        duration: 800,
        essential: true
      });
    }
  }, [selectedDPC?.id]);

  return (
    <div className="relative w-full h-full rounded-2xl overflow-hidden border border-gray-200 dark:border-slate-800 shadow-sm bg-gray-50 dark:bg-slate-950">
      {/* Map Mode Selector */}
      <div className="absolute top-3 left-3 z-10 bg-white/80 dark:bg-slate-900/80 backdrop-blur-xl rounded-xl p-1.5 shadow-lg border border-white/20 dark:border-slate-700 text-[11px] flex items-center font-bold">
        <button 
          onClick={() => setMapMode('default')} 
          className={`px-3 py-1.5 rounded-lg transition-all ${mapMode === 'default' ? 'bg-emerald-600 text-white shadow-md' : 'text-gray-600 dark:text-gray-300 hover:bg-black/5 dark:hover:bg-white/10'}`}
        >
          Default
        </button>
        <button 
          onClick={() => setMapMode('risk')} 
          className={`px-3 py-1.5 rounded-lg transition-all ${mapMode === 'risk' ? 'bg-emerald-600 text-white shadow-md' : 'text-gray-600 dark:text-gray-300 hover:bg-black/5 dark:hover:bg-white/10'}`}
        >
          Risk Zones
        </button>
        <button 
          onClick={() => setMapMode('satellite')} 
          className={`px-3 py-1.5 rounded-lg transition-all ${mapMode === 'satellite' ? 'bg-emerald-600 text-white shadow-md' : 'text-gray-600 dark:text-gray-300 hover:bg-black/5 dark:hover:bg-white/10'}`}
        >
          Satellite
        </button>
      </div>

      <Map
        ref={mapRef}
        initialViewState={{ longitude: THANJAVUR_CENTER[0], latitude: THANJAVUR_CENTER[1], zoom: DISTRICT_ZOOM }}
        maxBounds={THANJAVUR_BOUNDS}
        minZoom={8.2}
        maxZoom={15}
        scrollZoom={true}
        mapStyle={mapMode === 'satellite' ? satelliteStyle : (useFallbackStyle ? osmFallback : positron)}
        onLoad={onMapReady}
        onError={() => { if (!useFallbackStyle) setUseFallbackStyle(true); }}
        interactiveLayerIds={['dpc-nodes']}
        onMouseMove={handleMouseMove}
      >
        {/* 1. District boundary outline */}
        <Source id="thanjavur-district" type="geojson" data="/boundaries/thanjavur_boundaries.geojson">
          <Layer id="district-fill" type="fill" paint={{ 'fill-color': '#059669', 'fill-opacity': 0.03 }} />
          <Layer id="district-outline" type="line" paint={{ 'line-color': '#047857', 'line-width': 2.5, 'line-dasharray': [3, 2] }} />
        </Source>

        {/* 2. Village risk choropleth & Boundaries */}
        <Source id="village-risk" type="geojson" data="/boundaries/village_risk.geojson">
          <Layer
            id="village-risk-fill"
            type="fill"
            layout={{ visibility: mapMode === 'risk' ? 'visible' : 'none' }}
            paint={{
              'fill-color': [
                'interpolate', ['linear'], ['get', 'exposure_index'],
                0.0, '#16a34a',
                0.30, '#22c55e',
                0.38, '#eab308',
                0.45, '#f97316',
                0.55, '#ef4444',
                0.70, '#991b1b'
              ],
              'fill-opacity': 0.45
            }}
          />
        </Source>

        <Source id="thanjavur-boundaries" type="geojson" data="/boundaries/thanjavur_boundaries.geojson">
          <Layer
            id="village-boundaries-line"
            type="line"
            layout={{ visibility: mapMode !== 'default' ? 'visible' : 'none' }}
            paint={{
              'line-color': mapMode === 'satellite' ? '#ffffff' : '#9ca3af',
              'line-width': 0.5,
              'line-opacity': mapMode === 'satellite' ? 0.4 : 0.6
            }}
          />
        </Source>

        {/* 3. OSM road network */}
        <Source id="thanjavur-roads" type="geojson" data="/boundaries/thanjavur_roads.geojson">
          <Layer
            id="road-lines"
            type="line"
            layout={{ visibility: mapMode === 'default' ? 'visible' : 'none' }}
            paint={{
              'line-color': '#475569',
              'line-width': ['interpolate', ['linear'], ['zoom'], 9, 0.8, 12, 1.8],
              'line-opacity': 0.45
            }}
          />
        </Source>

        {/* 4. Selected DPC pulsing ring (below markers) */}
        <Source id="selected-ring" type="geojson" data={selectedGeojson as any}>
          <Layer
            id="selected-pulse"
            type="circle"
            paint={{
              'circle-color': 'transparent',
              'circle-stroke-color': '#2563eb',
              'circle-stroke-width': 2.5,
              'circle-radius': ['get', 'radius'],
              'circle-opacity': 0.7,
              'circle-stroke-opacity': 0.8
            }}
          />
        </Source>

        {/* 4.5 Relief Lines */}
        <Source id="relief-lines" type="geojson" data={reliefLinesGeojson as any}>
          <Layer
            id="relief-lines-layer"
            type="line"
            paint={{
              'line-color': '#3b82f6',
              'line-width': 2.5,
              'line-dasharray': [2, 2],
              'line-opacity': 0.8
            }}
          />
        </Source>

        {/* 5. DPC markers as Paddy Icons */}
        {dpcs.filter(d => d.lat != null && d.lon != null && !isNaN(Number(d.lat)) && !isNaN(Number(d.lon))).map((d) => {
          const isSelected = selectedDPC?.id === d.id;
          const meta = tierMeta[d.risk_tier as RiskTier] || tierMeta.GREEN;
          const isCritical = d.risk_tier === 'DARK_RED' || d.risk_tier === 'RED';
          
          // In Risk Zones mode, strictly hide non-critical centers
          if (mapMode === 'risk' && !isCritical) return null;

          return (
            <Marker
              key={d.id}
              longitude={Number(d.lon)}
              latitude={Number(d.lat)}
              anchor="bottom"
              onClick={(e) => {
                e.originalEvent.stopPropagation();
                onSelectDPC(d);
              }}
            >
              <div
                onMouseEnter={() => setHoveredDPC(d)}
                onMouseLeave={() => setHoveredDPC(null)}
                className={`relative flex items-center justify-center cursor-pointer transition-all duration-300 ${isSelected ? 'z-50 scale-125' : 'z-10 scale-100 hover:scale-110'}`}
                title={d.name}
              >
                {isSelected && (
                  <div className="absolute inset-0 rounded-full animate-ping opacity-75" style={{ backgroundColor: meta.color }}></div>
                )}
                <div 
                  className="relative w-6 h-6 rounded-full flex items-center justify-center shadow-md border-2 border-white text-[12px] bg-emerald-600"
                  style={{ backgroundColor: meta.color }}
                >
                  🌾
                </div>
              </div>
            </Marker>
          );
        })}

        <NavigationControl position="top-right" />

        {/* Hover tooltip */}
        {hoveredDPC && hoveredDPC.id !== selectedDPC?.id && !isNaN(Number(hoveredDPC.lon)) && !isNaN(Number(hoveredDPC.lat)) && (
          <Popup
            longitude={Number(hoveredDPC.lon)}
            latitude={Number(hoveredDPC.lat)}
            closeButton={false}
            closeOnClick={false}
            offset={14}
            className="z-50"
          >
            <div className="p-1.5 max-w-[220px] text-xs leading-relaxed">
              <div className="flex items-center justify-between gap-2 mb-1">
                <strong className="font-bold truncate">{hoveredDPC.name}</strong>
                <span
                  className="px-1.5 py-0.5 rounded text-[10px] font-bold text-white uppercase"
                  style={{ backgroundColor: (tierMeta[hoveredDPC.risk_tier as keyof typeof tierMeta] || tierMeta.GREEN).color }}
                >
                  {(tierMeta[hoveredDPC.risk_tier as keyof typeof tierMeta] || tierMeta.GREEN).label}
                </span>
              </div>
              <div className="text-gray-500 text-[11px]">{hoveredDPC.block}</div>
              <div className="mt-1 flex gap-3 text-[11px]">
                <span>Util: <b className={hoveredDPC.utilization_pct >= 90 ? 'text-rose-600' : ''}>{hoveredDPC.utilization_pct}%</b></span>
                <span>7D: <b>{hoveredDPC.expected_arrival_7d_mt} MT</b></span>
              </div>
            </div>
          </Popup>
        )}

        {/* Selected tooltip */}
        {selectedDPC && !isNaN(Number(selectedDPC.lon)) && !isNaN(Number(selectedDPC.lat)) && (
          <Popup
            longitude={Number(selectedDPC.lon)}
            latitude={Number(selectedDPC.lat)}
            closeButton={true}
            closeOnClick={false}
            onClose={() => onSelectDPC(null)}
            offset={16}
            className="z-50"
          >
            <div className="p-2 max-w-[260px] text-sm leading-relaxed text-gray-800 dark:text-gray-200">
              <div className="flex items-center justify-between gap-2 mb-2">
                <strong className="font-bold truncate">{selectedDPC.name}</strong>
                <span
                  className="px-2 py-1 rounded text-[10px] font-bold text-white uppercase"
                  style={{ backgroundColor: (tierMeta[selectedDPC.risk_tier as keyof typeof tierMeta] || tierMeta.GREEN).color }}
                >
                  {(tierMeta[selectedDPC.risk_tier as keyof typeof tierMeta] || tierMeta.GREEN).label}
                </span>
              </div>
              <div className="text-gray-500 text-xs mb-2">
                {selectedDPC.block} {selectedDPC.village ? `- ${selectedDPC.village}` : ''}
              </div>
              <div className="space-y-1 text-xs">
                <div className="flex justify-between">
                  <span>Capacity:</span> <span className="font-medium">{selectedDPC.capacity_mt} MT</span>
                </div>
                <div className="flex justify-between">
                  <span>Current Stock:</span> <span className="font-medium">{selectedDPC.current_stock_mt} MT</span>
                </div>
                <div className="flex justify-between">
                  <span>Utilization:</span> 
                  <span className={`font-bold ${selectedDPC.utilization_pct >= 90 ? 'text-rose-600' : ''}`}>
                    {selectedDPC.utilization_pct}%
                  </span>
                </div>
                <div className="flex justify-between">
                  <span>7D Forecast:</span> <span className="font-medium">{selectedDPC.expected_arrival_7d_mt} MT</span>
                </div>
                {selectedDPC.overflow_mt > 0 && (
                  <div className="flex justify-between text-rose-600 font-medium">
                    <span>Expected Overflow:</span> <span>{selectedDPC.overflow_mt} MT</span>
                  </div>
                )}
              </div>
            </div>
          </Popup>
        )}
      </Map>

      {/* Centre count badge */}
      <div className="absolute top-3 right-12 z-10 bg-white/90 dark:bg-slate-900/90 backdrop-blur-sm px-2.5 py-1 rounded-lg shadow-sm border border-gray-200 dark:border-slate-800 text-[11px] text-gray-600 dark:text-gray-300">
        <b className="text-emerald-700 dark:text-emerald-400">{dpcs.length}</b> centres
      </div>

      {/* Legend — dual legends when choropleth is on */}
      <div className="absolute bottom-3 left-3 right-3 z-10 flex items-end gap-2 flex-wrap">
        {/* DPC Operational Risk Tier legend */}
        <div className="bg-white/95 dark:bg-slate-900/95 backdrop-blur-md px-3 py-1.5 rounded-xl shadow-md border border-gray-200 dark:border-slate-800 flex items-center gap-2.5 text-[11px]">
          <span className="font-bold text-gray-500 dark:text-gray-400 text-[10px] uppercase tracking-wider">DPC Risk Tier</span>
          {(['DARK_RED', 'RED', 'YELLOW', 'GREEN'] as const).map(tier => (
            <span key={tier} className="flex items-center gap-1 font-medium text-gray-700 dark:text-gray-300">
              <span className="w-2 h-2 rounded-full inline-block" style={{ backgroundColor: tierMeta[tier].color }} />
              {tierMeta[tier].label}
            </span>
          ))}
        </div>

        {/* Choropleth legend */}
        {mapMode === 'risk' && (
          <div className="bg-white/95 dark:bg-slate-900/95 backdrop-blur-md px-3 py-1.5 rounded-xl shadow-md border border-gray-200 dark:border-slate-800 text-[11px]">
            <span className="font-bold text-gray-500 dark:text-gray-400 text-[10px] uppercase tracking-wider block mb-1">
              Area Flood & Access Exposure
            </span>
            <div className="flex items-center gap-1">
              <span className="text-[10px] text-gray-500">Low</span>
              <div className="w-24 h-2 rounded-full" style={{
                background: 'linear-gradient(to right, #22c55e, #eab308, #f97316, #ef4444)'
              }} />
              <span className="text-[10px] text-gray-500">Critical</span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
