import logging
import config  # Assuming config.py is at the root and handles .env loading

from vector_store_base import VectorStoreBase
from vector_search_wrapper import VectorSearch # Assuming vs is the global instance
from chromadb_wrapper import ChromaDB     # Assuming cdb is the global instance

logger = logging.getLogger(__name__)

# Global instances, similar to how they might have been used before.
# These will be instantiated by the factory based on config.
# However, the factory should return a new instance each time or a singleton if desired.
# For now, the factory will return new instances of the specific classes.
# The global `vs` and `cdb` instances in their respective wrapper modules might become obsolete
# or could be managed differently if the factory is the sole provider.
# Let's assume the factory is the new way to get these.

def get_vector_store() -> VectorStoreBase:
    """
    Factory function to get an instance of the configured vector store.

    Reads the VECTOR_STORE setting from the application configuration (config.py)
    and returns an appropriate implementation of VectorStoreBase.

    Raises:
        ValueError: If the configured VECTOR_STORE is not recognized.

    Returns:
        VectorStoreBase: An instance of the configured vector store wrapper.
    """
    vector_store_name = config.VECTOR_STORE
    logger.info(f"Attempting to instantiate vector store: {vector_store_name}")

    if vector_store_name == "VECTOR_SEARCH":
        logger.info("VECTOR_STORE is 'VECTOR_SEARCH'. Instantiating VectorSearch.")
        # The VectorSearch class itself uses config for its defaults.
        return VectorSearch()
    elif vector_store_name == "CHROMADB":
        logger.info("VECTOR_STORE is 'CHROMADB'. Instantiating ChromaDB.")
        # The ChromaDB class itself uses config for its defaults.
        return ChromaDB()
    else:
        error_message = (
            f"Invalid VECTOR_STORE configuration: '{vector_store_name}'. "
            "Supported values are 'VECTOR_SEARCH' or 'CHROMADB'."
        )
        logger.error(error_message)
        raise ValueError(error_message)

# Example of how this might be used (optional, for testing or if this module becomes an entry point for it)
# if __name__ == "__main__":
#     # Ensure logging is configured if running standalone for test
#     logging.basicConfig(level=logging.INFO)
#
#     try:
#         # This relies on config.py successfully loading .env or environment variables
#         vector_store_instance = get_vector_store()
#         logger.info(f"Successfully instantiated vector store of type: {type(vector_store_instance).__name__}")
#         # You could add a simple test query here if the underlying services are up
#         # For example:
#         # if hasattr(vector_store_instance, 'query'):
#         #     dummy_vector = [0.1] * 1408 # Adjust dimension if needed
#         #     results = vector_store_instance.query(vector=dummy_vector, top_k=1)
#         #     logger.info(f"Test query results: {results}")
#     except ValueError as e:
#         logger.error(f"Factory configuration error: {e}")
#     except Exception as e:
#         logger.error(f"An unexpected error occurred: {e}")
