import sys
import os

# Add backend to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.main import app
from mangum import Mangum

handler = Mangum(app)
