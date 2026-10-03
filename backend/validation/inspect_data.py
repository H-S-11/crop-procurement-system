import pandas as pd

b10_path = "../data/B10_damage_incident_register_Thanjavur.csv"
b11_path = "../data/B11_road_closure_events_Thanjavur.csv"

if __name__ == "__main__":
    try:
        b10 = pd.read_csv(b10_path)
        print("B10 Shape:", b10.shape)
        print("B10 Columns:", b10.columns.tolist())
        print("B10 Date Range:", b10['date'].min(), "to", b10['date'].max())
    except Exception as e:
        print("Error reading B10:", e)
        
    try:
        b11 = pd.read_csv(b11_path)
        print("B11 Shape:", b11.shape)
        print("B11 Columns:", b11.columns.tolist())
        print("B11 Date Range:", b11['date'].min(), "to", b11['date'].max())
    except Exception as e:
        print("Error reading B11:", e)
