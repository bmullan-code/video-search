import os
from dotenv import load_dotenv
import logging

# Configure logger for this module
logger = logging.getLogger(__name__)

# Load environment variables from .env file
loaded_dotenv = load_dotenv()

if loaded_dotenv:
    logger.info(".env file loaded successfully.")
else:
    logger.info(".env file not found or is empty. Relying on environment variables or defaults.")

# Define configuration constants
PROJECT_ID = os.getenv("PROJECT_ID")
LOCATION = os.getenv("LOCATION")
BUCKET_NAME = os.getenv("BUCKET_NAME")
MULTIMODAL_EMBEDDING_MODEL = os.getenv("MULTIMODAL_EMBEDDING_MODEL")
GEMINI_MODEL_ID = os.getenv("GEMINI_MODEL_ID")

VECTOR_STORE = os.getenv("VECTOR_STORE")

# Vector Search specific (may be None if ChromaDB is used)
VECTOR_SEARCH_INDEX = os.getenv("VECTOR_SEARCH_INDEX")
DEPLOYED_INDEX_ID = os.getenv("DEPLOYED_INDEX_ID")
INDEX_ENDPOINT_ID = os.getenv("INDEX_ENDPOINT_ID")

# ChromaDB specific (may be None if Vector Search is used)
CHROMADB_COLLECTION_NAME = os.getenv("CHROMADB_COLLECTION_NAME")

# Log loaded values (optional, for debugging - be careful with sensitive data in logs)
# logger.info(f"PROJECT_ID: {PROJECT_ID}")
# logger.info(f"LOCATION: {LOCATION}")
# logger.info(f"BUCKET_NAME: {BUCKET_NAME}")
# logger.info(f"VECTOR_STORE: {VECTOR_STORE}")


# --- Validate critical configurations ---
critical_vars = {
    "PROJECT_ID": PROJECT_ID,
    "LOCATION": LOCATION,
    "BUCKET_NAME": BUCKET_NAME,
    "VECTOR_STORE": VECTOR_STORE,
}

missing_vars = [name for name, value in critical_vars.items() if value is None]

if missing_vars:
    error_message = f"Missing critical environment variables: {', '.join(missing_vars)}. Please set them in .env file or environment."
    logger.error(error_message)
    raise ValueError(error_message)
else:
    logger.info("Critical configurations successfully loaded and validated.")

# --- Additional checks based on VECTOR_STORE value ---
if VECTOR_STORE == "VECTOR_SEARCH":
    logger.info("VECTOR_STORE is 'VECTOR_SEARCH'. Checking related variables.")
    vector_search_critical_vars = {
        "VECTOR_SEARCH_INDEX": VECTOR_SEARCH_INDEX,
        "DEPLOYED_INDEX_ID": DEPLOYED_INDEX_ID,
        "INDEX_ENDPOINT_ID": INDEX_ENDPOINT_ID,
    }
    missing_vs_vars = [name for name, value in vector_search_critical_vars.items() if value is None]
    if missing_vs_vars:
        vs_error_message = f"Missing VECTOR_SEARCH specific environment variables: {', '.join(missing_vs_vars)}."
        logger.error(vs_error_message)
        raise ValueError(vs_error_message)
    else:
        logger.info("VECTOR_SEARCH specific configurations successfully loaded.")

elif VECTOR_STORE == "CHROMADB":
    logger.info("VECTOR_STORE is 'CHROMADB'. Checking related variables.")
    chromadb_critical_vars = {
        "CHROMADB_COLLECTION_NAME": CHROMADB_COLLECTION_NAME,
    }
    missing_chroma_vars = [name for name, value in chromadb_critical_vars.items() if value is None]
    if missing_chroma_vars:
        chroma_error_message = f"Missing CHROMADB specific environment variable: {', '.join(missing_chroma_vars)}."
        logger.error(chroma_error_message)
        raise ValueError(chroma_error_message)
    else:
        logger.info("CHROMADB specific configurations successfully loaded.")

else:
    # If VECTOR_STORE is set to something else, or not set but passed the initial critical check (won't happen due to check above)
    if VECTOR_STORE is not None: # only raise if it's an unknown value
        unknown_vs_error = f"Unknown VECTOR_STORE value: '{VECTOR_STORE}'. Must be 'VECTOR_SEARCH' or 'CHROMADB'."
        logger.error(unknown_vs_error)
        raise ValueError(unknown_vs_error)

logger.info("Configuration loading complete.")
