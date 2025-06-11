import unittest
import os
import importlib
from unittest.mock import patch

# Assuming 'config.py' and other project modules are discoverable.
import config
# We need to import vector_store_factory after config might have been reloaded
# so it's better to import it within test methods or setUp after reloading config.

class TestVectorStoreFactory(unittest.TestCase):

    # Define common environment variable structures for tests
    # These ensure that config.py can load successfully before the factory is tested.
    base_critical_vars = {
        "PROJECT_ID": "test_project",
        "LOCATION": "test_location",
        "BUCKET_NAME": "test_bucket",
        # Non-critical but often present
        "GEMINI_MODEL_ID": "test_gemini",
        "MULTIMODAL_EMBEDDING_MODEL": "test_mm_emb"
    }

    vector_search_env_vars = {
        **base_critical_vars,
        "VECTOR_STORE": "VECTOR_SEARCH",
        "VECTOR_SEARCH_INDEX": "test_vs_index",
        "DEPLOYED_INDEX_ID": "test_vs_deployed_id",
        "INDEX_ENDPOINT_ID": "test_vs_endpoint_id",
    }

    chromadb_env_vars = {
        **base_critical_vars,
        "VECTOR_STORE": "CHROMADB",
        "CHROMADB_COLLECTION_NAME": "test_chroma_collection",
    }

    invalid_store_env_vars = {
        **base_critical_vars,
        "VECTOR_STORE": "INVALID_STORE",
        # Include other vars to ensure config itself doesn't fail before factory logic
        "VECTOR_SEARCH_INDEX": "dummy",
        "DEPLOYED_INDEX_ID": "dummy",
        "INDEX_ENDPOINT_ID": "dummy",
        "CHROMADB_COLLECTION_NAME": "dummy",
    }

    # This variable will hold the module loaded with patched env
    # It's important because vector_store_factory imports config at its module level.
    # So, we need to reload vector_store_factory itself after config is reloaded.
    patched_vector_store_factory = None

    @patch.dict(os.environ, vector_search_env_vars, clear=True)
    def test_returns_vector_search_instance(self):
        """Test factory returns VectorSearch instance for VECTOR_STORE=VECTOR_SEARCH."""
        importlib.reload(config)

        # Reload vector_store_factory to pick up the reloaded config
        import vector_store_factory
        importlib.reload(vector_store_factory)

        from vector_search_wrapper import VectorSearch # For type assertion

        store = vector_store_factory.get_vector_store()
        self.assertIsInstance(store, VectorSearch)

    @patch.dict(os.environ, chromadb_env_vars, clear=True)
    def test_returns_chromadb_instance(self):
        """Test factory returns ChromaDB instance for VECTOR_STORE=CHROMADB."""
        importlib.reload(config)

        import vector_store_factory
        importlib.reload(vector_store_factory)

        from chromadb_wrapper import ChromaDB # For type assertion

        store = vector_store_factory.get_vector_store()
        self.assertIsInstance(store, ChromaDB)

    @patch.dict(os.environ, invalid_store_env_vars, clear=True)
    def test_raises_value_error_for_invalid_store_config_value(self):
        """Test factory raises ValueError for an unrecognized VECTOR_STORE value."""
        importlib.reload(config)

        import vector_store_factory
        importlib.reload(vector_store_factory)

        with self.assertRaisesRegex(ValueError, "Invalid VECTOR_STORE configuration: 'INVALID_STORE'"):
            vector_store_factory.get_vector_store()

    # Test Case: What if config.VECTOR_STORE is None due to it not being set and not critical?
    # Current config.py makes VECTOR_STORE a critical var, so it would raise ValueError itself.
    # If VECTOR_STORE was NOT critical in config.py and was None:
    # @patch.dict(os.environ, base_critical_vars, clear=True) # VECTOR_STORE is not set
    # def test_handles_vector_store_not_set_in_config(self):
    #     """Test factory behavior if VECTOR_STORE is None (e.g., not set in env)."""
    #     # With current config.py, this test is tricky because config.py itself will fail.
    #     # To test factory in isolation for this, we'd mock config.VECTOR_STORE directly.
    #     importlib.reload(config) # This would fail if VECTOR_STORE is critical and missing

    #     import vector_store_factory
    #     importlib.reload(vector_store_factory)

    #     # If config.py allows VECTOR_STORE to be None:
    #     # get_vector_store() would try to access config.VECTOR_STORE (None)
    #     # and then hit the 'else' in the factory, raising ValueError.
    #     with patch.object(config, 'VECTOR_STORE', None): # Directly mock config.VECTOR_STORE
    #         importlib.reload(vector_store_factory) # Reload factory to see mocked config attr
    #         with self.assertRaisesRegex(ValueError, "Invalid VECTOR_STORE configuration: 'None'"):
    #             vector_store_factory.get_vector_store()


if __name__ == '__main__':
    unittest.main()
