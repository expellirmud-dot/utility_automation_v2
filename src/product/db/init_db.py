import os
import sys

# Ensure project root is in python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

from src.product.db.session import engine
from src.product.db.models import Base

def init_db():
    # Create all tables in the product.db
    Base.metadata.create_all(bind=engine)
    print("Product database initialized successfully at data/product.db")

if __name__ == "__main__":
    init_db()
