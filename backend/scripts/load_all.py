import load_villages
import load_roads
import load_dpcs
import load_rainfall
import load_sar_flood
import load_arrivals
import load_godown_ledger
import load_inventory
import load_road_closures
import load_damage_incidents
import load_provenance

if __name__ == '__main__':
    load_villages.load()
    load_roads.load()
    load_dpcs.load()
    load_rainfall.load()
    load_sar_flood.load()
    load_arrivals.load()
    # load_godown_ledger.load()
    # load_inventory.load()
    # load_road_closures.load()
    # load_damage_incidents.load()
    # load_provenance.load()
    print("All loads complete!")
