from database import SessionLocal
from models import DamageIncident, RoadClosure

db = SessionLocal()
print("Damage Incidents:", db.query(DamageIncident).count())
print("Road Closures:", db.query(RoadClosure).count())
db.close()
