# db_config.py
from pymongo import MongoClient

usuario = ""
contrasena = ""

try:
    cliente = MongoClient(
        f"mongodb+srv://{usuario}:{contrasena}@cluster0.n8op7pt.mongodb.net/?retryWrites=true&w=majority"
    )
    db = cliente["Lizama_car"]  
    print("✅ Conexión exitosa a MongoDB Atlas")
except Exception as e:
    print("❌ Error de conexión con MongoDB Atlas:", e)
