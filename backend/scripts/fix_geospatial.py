"""
Reproject Thanjavur boundaries to EPSG:4326 (WGS84),
generate Thanjavur district boundary polygon,
and extract Thanjavur major road network from GeoPackage.
"""
import os
import json
import sqlite3
import rasterio.warp

DATA_DIR = os.path.join(os.path.dirname(__file__), '../../data')
BOUNDARIES_IN = os.path.join(DATA_DIR, 'boundaries/thanjavur_boundaries.geojson')
BOUNDARIES_OUT = os.path.join(DATA_DIR, 'boundaries/thanjavur_boundaries_wgs84.geojson')
DISTRICT_OUT = os.path.join(DATA_DIR, 'boundaries/thanjavur_district.geojson')
ROADS_OUT = os.path.join(DATA_DIR, 'boundaries/thanjavur_roads.geojson')

PUBLIC_BOUNDARIES = os.path.join(os.path.dirname(__file__), '../../frontend/public/boundaries')
os.makedirs(PUBLIC_BOUNDARIES, exist_ok=True)

def reproject_boundaries():
    print(f"Reading {BOUNDARIES_IN}...")
    with open(BOUNDARIES_IN, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    features = data.get('features', [])
    print(f"Total features to reproject: {len(features)}")
    
    reprojected_features = []
    
    for i, feat in enumerate(features):
        geom = feat.get('geometry')
        if not geom:
            continue
        try:
            wgs84_geom = rasterio.warp.transform_geom('EPSG:7755', 'EPSG:4326', geom)
            feat['geometry'] = wgs84_geom
            # Strip newline from state_name
            if 'properties' in feat and feat['properties']:
                props = feat['properties']
                if 'state_name' in props and isinstance(props['state_name'], str):
                    props['state_name'] = props['state_name'].strip()
            reprojected_features.append(feat)
        except Exception as e:
            if i < 5:
                print(f"Error reprojecting feature {i}: {e}")
            continue

    wgs84_data = {
        "type": "FeatureCollection",
        "name": "thanjavur_village_boundaries",
        "crs": {
            "type": "name",
            "properties": {
                "name": "urn:ogc:def:crs:OGC:1.3:CRS84"
            }
        },
        "features": reprojected_features
    }
    
    with open(BOUNDARIES_OUT, 'w', encoding='utf-8') as f:
        json.dump(wgs84_data, f)
    print(f"Saved reprojected boundaries to {BOUNDARIES_OUT}")
    
    # Also overwrite the frontend public boundaries file
    target_frontend = os.path.join(PUBLIC_BOUNDARIES, 'thanjavur_boundaries.geojson')
    with open(target_frontend, 'w', encoding='utf-8') as f:
        json.dump(wgs84_data, f)
    print(f"Saved reprojected boundaries to {target_frontend}")
    
    # Calculate district bounding box and convex hull / simplified polygon
    # Collect all coords to compute bbox
    all_lons = []
    all_lats = []
    for feat in reprojected_features:
        geom = feat['geometry']
        def extract_coords(coords):
            if isinstance(coords[0], (int, float)):
                all_lons.append(coords[0])
                all_lats.append(coords[1])
            else:
                for c in coords:
                    extract_coords(c)
        extract_coords(geom['coordinates'])
        
    min_lon, max_lon = min(all_lons), max(all_lons)
    min_lat, max_lat = min(all_lats), max(all_lats)
    print(f"Thanjavur Extent: Lon [{min_lon:.4f}, {max_lon:.4f}], Lat [{min_lat:.4f}, {max_lat:.4f}]")
    
    # Create a simplified district outline feature collection
    district_data = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {
                    "district": "Thanjavur",
                    "state": "Tamil Nadu",
                    "total_villages": len(reprojected_features)
                },
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [min_lon, min_lat],
                        [max_lon, min_lat],
                        [max_lon, max_lat],
                        [min_lon, max_lat],
                        [min_lon, min_lat]
                    ]]
                }
            }
        ]
    }
    with open(DISTRICT_OUT, 'w', encoding='utf-8') as f:
        json.dump(district_data, f)
    with open(os.path.join(PUBLIC_BOUNDARIES, 'thanjavur_district.geojson'), 'w', encoding='utf-8') as f:
        json.dump(district_data, f)
    print("District boundary generated.")

def extract_roads():
    gpkg_path = os.path.join(DATA_DIR, 'road_network/planet_78.80,9.85_79.58,11.20-geopackage/planet_78.80,9.85_79.58,11.20.gpkg')
    if not os.path.exists(gpkg_path):
        print("Roads geopackage not found.")
        return

    print("Extracting major roads from GeoPackage...")
    conn = sqlite3.connect(gpkg_path)
    c = conn.cursor()
    
    # Query lines table for highway types: motorway, trunk, primary, secondary
    # In OSM GeoPackage, lines table has geometry column 'geom' in WKB or GPKG binary geometry
    try:
        c.execute("PRAGMA table_info(lines)")
        cols = [r[1] for r in c.fetchall()]
        print("Lines columns:", cols[:10])
        
        # Check highways
        c.execute("""
            SELECT osm_id, name, highway, typeof(geom), length(geom)
            FROM lines
            WHERE highway IN ('trunk', 'primary', 'secondary', 'trunk_link', 'primary_link')
            LIMIT 5
        """)
        rows = c.fetchall()
        print("Sample major roads:", [(r[0], r[1], r[2]) for r in rows])
        
        # In GPKG, geom has a header (8 bytes magic, 4 bytes srs_id, envelope, etc.), then standard WKB
        # Let's decode WKB to GeoJSON
        c.execute("""
            SELECT osm_id, name, highway, geom
            FROM lines
            WHERE highway IN ('trunk', 'primary', 'secondary', 'tertiary')
        """)
        all_roads = c.fetchall()
        print(f"Total major roads found: {len(all_roads)}")
        
        road_features = []
        for r in all_roads:
            osm_id, name, highway, blob = r
            if not blob or len(blob) < 8:
                continue
            
            # GPKG geometry binary header:
            # bytes 0-1: 0x47, 0x50 ('GP')
            # byte 2: version (0)
            # byte 3: flags
            # byte 4-7: srs_id (int32 little endian)
            flags = blob[3]
            envelope_type = (flags >> 1) & 0x07
            # envelope byte size: 0: 0, 1: 32, 2: 48, 3: 48, 4: 64
            envelope_sizes = {0: 0, 1: 32, 2: 48, 3: 48, 4: 64}
            env_size = envelope_sizes.get(envelope_type, 0)
            wkb_start = 8 + env_size
            wkb = blob[wkb_start:]
            
            # Simple WKB LineString parser:
            # byte 0: byte order (1 = Little Endian)
            # byte 1-4: geom type (2 = LineString, 2D)
            # byte 5-8: numPoints (uint32)
            # followed by pairs of double (X, Y)
            if len(wkb) >= 9:
                import struct
                byte_order = wkb[0]
                endian = '<' if byte_order == 1 else '>'
                geom_type = struct.unpack(endian + 'I', wkb[1:5])[0]
                if geom_type in (2, 1002): # LineString
                    num_points = struct.unpack(endian + 'I', wkb[5:9])[0]
                    expected_len = 9 + num_points * 16
                    if len(wkb) >= expected_len:
                        coords = []
                        for pi in range(num_points):
                            px, py = struct.unpack(endian + 'dd', wkb[9 + pi*16 : 9 + (pi+1)*16])
                            coords.append([round(px, 5), round(py, 5)])
                        road_features.append({
                            "type": "Feature",
                            "properties": {
                                "id": osm_id,
                                "name": name or "Unnamed Road",
                                "highway": highway
                            },
                            "geometry": {
                                "type": "LineString",
                                "coordinates": coords
                            }
                        })
        
        print(f"Decoded {len(road_features)} LineString road features.")
        roads_geojson = {
            "type": "FeatureCollection",
            "features": road_features
        }
        with open(ROADS_OUT, 'w', encoding='utf-8') as f:
            json.dump(roads_geojson, f)
        with open(os.path.join(PUBLIC_BOUNDARIES, 'thanjavur_roads.geojson'), 'w', encoding='utf-8') as f:
            json.dump(roads_geojson, f)
        print("Roads GeoJSON exported successfully.")
    except Exception as e:
        print(f"Error extracting roads: {e}")
    finally:
        conn.close()

if __name__ == '__main__':
    reproject_boundaries()
    extract_roads()
