import sys
import os
import shutil

# Add backend directory and root directory to sys.path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
backend_dir = os.path.join(root_dir, "backend")
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

# Set environment variables for serverless execution
os.environ.setdefault("TESTING", "0")
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

# Detect serverless environment (Vercel, AWS Lambda)
is_serverless = bool(os.environ.get("VERCEL") or os.environ.get("AWS_LAMBDA_FUNCTION_NAME"))
if is_serverless:
    os.environ["VERCEL"] = "1"
    tmp_db = "/tmp/ghajini.db"
    src_db = os.path.join(root_dir, "ghajini.db")
    if not os.path.exists(tmp_db) and os.path.exists(src_db):
        try:
            shutil.copy2(src_db, tmp_db)
        except Exception:
            pass
    os.environ["DATABASE_URL"] = f"sqlite:///{tmp_db}"
    os.environ["DATA_DIR"] = "/tmp/data"
    os.environ["UPLOAD_DIR"] = "/tmp/data/uploads"

# Import the main FastAPI application
from app.main import app
