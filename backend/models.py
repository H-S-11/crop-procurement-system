from sqlalchemy import Column, Integer, String, Float, Boolean, Date, ForeignKey, DateTime
from sqlalchemy.orm import declarative_base, relationship
from geoalchemy2 import Geometry

Base = declarative_base()

class Village(Base):
    __tablename__ = 'villages'
    id = Column(String, primary_key=True) # or Integer based on actual data
    name = Column(String)
    geom = Column(Geometry(geometry_type='GEOMETRY', srid=4326, spatial_index=True))
    block = Column(String)
    paddy_area_ha = Column(Float)
    expected_yield = Column(Float)

class Road(Base):
    __tablename__ = 'roads'
    id = Column(String, primary_key=True)
    geom = Column(Geometry(geometry_type='LINESTRING', srid=4326, spatial_index=True))
    road_class = Column(String)
    source = Column(String)

class DPC(Base):
    __tablename__ = 'dpcs'
    id = Column(String, primary_key=True)
    name = Column(String)
    geom = Column(Geometry(geometry_type='POINT', srid=4326, spatial_index=True))
    capacity_mt = Column(Float, default=250)
    block = Column(String)
    village_id = Column(String, ForeignKey('villages.id'), nullable=True)
    road_distance_m = Column(Float)
    elevation_m = Column(Float)
    flood_risk_class = Column(String)
    design_area_cents = Column(Float)
    # Note: Spatial calculations (distance, area) should reproject to EPSG:32644 (UTM 44N). Do not compute directly in 4326.

class DemRaster(Base):
    __tablename__ = 'dem_rasters'
    id = Column(Integer, primary_key=True, autoincrement=True)
    filename = Column(String)
    filepath = Column(String)
    bounds_geom = Column(Geometry(geometry_type='POLYGON', srid=4326, spatial_index=True), nullable=True)

class SarFloodRaster(Base):
    __tablename__ = 'sar_flood_rasters'
    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date, nullable=True)
    filename = Column(String)
    filepath = Column(String)
    source = Column(String)

class RainfallObservation(Base):
    __tablename__ = 'rainfall_observations'
    id = Column(Integer, primary_key=True, autoincrement=True)
    station_id = Column(String)
    date = Column(Date)
    rainfall_mm = Column(Float)
    geom = Column(Geometry(geometry_type='POINT', srid=4326, spatial_index=True))

class Arrival(Base):
    __tablename__ = 'arrivals'
    id = Column(Integer, primary_key=True, autoincrement=True)
    dpc_id = Column(String, ForeignKey('dpcs.id'), index=True)
    date = Column(Date, index=True)
    mt_arrived = Column(Float)
    moisture_pct = Column(Float, nullable=True)

class GodownLedger(Base):
    __tablename__ = 'godown_ledger'
    id = Column(String, primary_key=True)
    godown_id = Column(String)
    date = Column(Date)
    occupancy_mt = Column(Float)
    capacity_mt = Column(Float)

class InventoryGunnyTarpaulin(Base):
    __tablename__ = 'inventory_gunny_tarpaulin'
    id = Column(Integer, primary_key=True, autoincrement=True)
    dpc_id = Column(String, ForeignKey('dpcs.id'), index=True)
    date = Column(Date, index=True)
    gunny_bags_available = Column(Float)
    tarpaulin_available = Column(Float)

class RoadClosure(Base):
    __tablename__ = 'road_closures'
    id = Column(String, primary_key=True)
    road_id = Column(String, ForeignKey('roads.id'), nullable=True)
    dpc_id = Column(String, ForeignKey('dpcs.id'), nullable=True)
    date_start = Column(Date)
    date_end = Column(Date, nullable=True)
    reason = Column(String)
    geom = Column(Geometry(geometry_type='GEOMETRY', srid=4326, spatial_index=True), nullable=True)

class DamageIncident(Base):
    __tablename__ = 'damage_incidents'
    id = Column(String, primary_key=True)
    dpc_id = Column(String, ForeignKey('dpcs.id'))
    date = Column(Date)
    tonnage_damaged = Column(Float)
    cause = Column(String)
    source = Column(String)

class DataProvenance(Base):
    __tablename__ = 'data_provenance'
    layer = Column(String, primary_key=True)
    source_type = Column(String)
    generating_process = Column(String)
    reconciliation_anchor = Column(String)
    confidence = Column(String)

class DpcFeatureStore(Base):
    __tablename__ = 'dpc_feature_store'
    id = Column(Integer, primary_key=True, autoincrement=True)
    dpc_id = Column(String, ForeignKey('dpcs.id'), index=True)
    date = Column(Date, index=True)
    geom = Column(Geometry(geometry_type='POINT', srid=4326))
    block = Column(String)
    village = Column(String)
    capacity = Column(Float)
    elevation = Column(Float)
    elevation_percentile = Column(Float)
    nearest_road_distance_m = Column(Float)
    road_density_1km = Column(Float)
    road_density_5km = Column(Float)
    major_road_distance_m = Column(Float)
    flood_exposure = Column(Float)
    flood_frequency = Column(Float)
    rainfall_3d = Column(Float)
    rainfall_7d = Column(Float)
    rainfall_14d = Column(Float)
    rainfall_30d = Column(Float)
    rainy_days_7d = Column(Float)
    arrival_7d_mean = Column(Float)
    arrival_7d_max = Column(Float)
    arrival_14d_mean = Column(Float)
    arrival_volatility = Column(Float)
    season_id = Column(String)
    feature_generated_at = Column(DateTime)
