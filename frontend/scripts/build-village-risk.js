#!/usr/bin/env node
/**
 * build-village-risk.js
 *
 * Derives a village-level "flood & access exposure" index from:
 *   - flood_exposure_pct (HAND flood index via Sentinel-1)
 *   - rainfall_7d_mm (7-day cumulative rainfall)
 *   - access_disrupted (road-distance/access fragility)
 *
 * Each village polygon gets the index of the nearest DPC that shares
 * its block (panchayat union), or the geographically nearest DPC if
 * no block match exists. This is a spatial proximity attribution, NOT
 * a claim that the DPC risk *is* the village risk — it's labeled separately.
 *
 * Output: public/boundaries/village_risk.geojson
 */

const fs = require('fs');
const path = require('path');

const DEMO_DATA = path.join(__dirname, '..', 'public', 'demo-data.json');
const VILLAGE_GEOJSON = path.join(__dirname, '..', 'public', 'boundaries', 'thanjavur_boundaries.geojson');
const OUTPUT = path.join(__dirname, '..', 'public', 'boundaries', 'village_risk.geojson');

// Load data
const demoData = JSON.parse(fs.readFileSync(DEMO_DATA, 'utf-8'));
const villageGeo = JSON.parse(fs.readFileSync(VILLAGE_GEOJSON, 'utf-8'));

const dpcs = demoData.dpcs.filter(d => d.is_active_season);

// Compute per-DPC raw exposure components (0-1 each)
const maxRainfall = Math.max(...dpcs.map(d => d.rainfall_7d_mm || 0), 1);

const dpcExposures = dpcs.map(d => {
  // Flood: flood_exposure_pct is already 0-100
  const flood = Math.min((d.flood_exposure_pct || 0) / 100, 1);
  // Rainfall: normalized to max observed
  const rain = Math.min((d.rainfall_7d_mm || 0) / maxRainfall, 1);
  // Access fragility: binary flag
  const access = d.access_disrupted ? 1 : 0;

  // Composite: 50% flood, 30% rainfall, 20% access
  const index = flood * 0.5 + rain * 0.3 + access * 0.2;

  return {
    ...d,
    _flood: flood,
    _rain: rain,
    _access: access,
    _exposure_index: Math.round(index * 100) / 100
  };
});

// Haversine distance (km)
function haversine(lat1, lon1, lat2, lon2) {
  const R = 6371;
  const dLat = (lat2 - lat1) * Math.PI / 180;
  const dLon = (lon2 - lon1) * Math.PI / 180;
  const a = Math.sin(dLat/2)**2 + Math.cos(lat1*Math.PI/180)*Math.cos(lat2*Math.PI/180)*Math.sin(dLon/2)**2;
  return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
}

// Centroid of a MultiPolygon
function centroid(geometry) {
  let sumLat = 0, sumLon = 0, count = 0;
  const coords = geometry.type === 'MultiPolygon' ? geometry.coordinates : [geometry.coordinates];
  for (const poly of coords) {
    for (const ring of poly) {
      for (const [lon, lat] of ring) {
        sumLon += lon;
        sumLat += lat;
        count++;
      }
    }
  }
  return [sumLat / count, sumLon / count];
}

// For each village, find the best matching DPC
const outputFeatures = villageGeo.features.map(f => {
  const vBlock = (f.properties.block || '').toLowerCase().trim();
  const [vLat, vLon] = centroid(f.geometry);

  // 1. Try block-matched DPCs first
  const blockMatches = dpcExposures.filter(d =>
    (d.block || '').toLowerCase().trim() === vBlock
  );

  let bestDPC;
  if (blockMatches.length > 0) {
    // Among block matches, pick the nearest
    bestDPC = blockMatches.reduce((best, d) => {
      const dist = haversine(vLat, vLon, d.lat, d.lon);
      return dist < best.dist ? { dpc: d, dist } : best;
    }, { dpc: blockMatches[0], dist: Infinity }).dpc;
  } else {
    // Fallback: nearest DPC by geography
    bestDPC = dpcExposures.reduce((best, d) => {
      const dist = haversine(vLat, vLon, d.lat, d.lon);
      return dist < best.dist ? { dpc: d, dist } : best;
    }, { dpc: dpcExposures[0], dist: Infinity }).dpc;
  }

  return {
    type: 'Feature',
    properties: {
      village: f.properties.village,
      block: f.properties.block,
      exposure_index: bestDPC._exposure_index,
      flood_component: bestDPC._flood,
      rainfall_component: bestDPC._rain,
      access_component: bestDPC._access,
      nearest_dpc: bestDPC.name,
      rainfall_7d_mm: bestDPC.rainfall_7d_mm,
      flood_exposure_pct: bestDPC.flood_exposure_pct
    },
    geometry: f.geometry
  };
});

const output = {
  type: 'FeatureCollection',
  features: outputFeatures
};

fs.writeFileSync(OUTPUT, JSON.stringify(output));
console.log(`✓ Wrote ${outputFeatures.length} village risk polygons to ${OUTPUT}`);
console.log(`  Index range: ${Math.min(...outputFeatures.map(f=>f.properties.exposure_index)).toFixed(2)} – ${Math.max(...outputFeatures.map(f=>f.properties.exposure_index)).toFixed(2)}`);
