import os

# Set testing environment flag immediately before any test or app module imports
os.environ["TESTING"] = "1"
os.environ["HF_HUB_OFFLINE"] = "1"
