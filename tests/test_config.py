import unittest
import os
import importlib
from unittest.mock import patch

# Ensure the path is set up correctly if 'config' is not in the default Python path
# For this environment, assuming 'config.py' is at the root and discoverable.
import config

class TestConfig(unittest.TestCase):

    # Store original environ to restore if absolutely necessary, though patch.dict should handle it
    # original_environ = None

    # @classmethod
    # def setUpClass(cls):
    #     cls.original_environ = os.environ.copy()

    # @classmethod
    # def tearDownClass(cls):
    #     os.environ.clear()
    #     os.environ.update(cls.original_environ)

    common_critical_vars = {
        "PROJECT_ID": "test_project",
        "LOCATION": "test_location",
        "BUCKET_NAME": "test_bucket",
        # GEMINI_MODEL_ID and MULTIMODAL_EMBEDDING_MODEL are not in critical_vars check in config.py
        "GEMINI_MODEL_ID": "test_gemini",
        "MULTIMODAL_EMBEDDING_MODEL": "test_mm_emb"
    }

    vector_search_specific_vars = {
        "VECTOR_SEARCH_INDEX": "test_vs_index",
        "DEPLOYED_INDEX_ID": "test_vs_deployed_id",
        "INDEX_ENDPOINT_ID": "test_vs_endpoint_id",
    }

    chromadb_specific_vars = {
        "CHROMADB_COLLECTION_NAME": "test_chroma_collection",
    }

    @patch.dict(os.environ, {
        **common_critical_vars,
        "VECTOR_STORE": "VECTOR_SEARCH",
        **vector_search_specific_vars
    }, clear=True)
    def test_successful_load_vector_search(self):
        """Test successful loading with VECTOR_STORE=VECTOR_SEARCH and all required vars."""
        importlib.reload(config)
        self.assertEqual(config.PROJECT_ID, "test_project")
        self.assertEqual(config.LOCATION, "test_location")
        self.assertEqual(config.BUCKET_NAME, "test_bucket")
        self.assertEqual(config.VECTOR_STORE, "VECTOR_SEARCH")
        self.assertEqual(config.VECTOR_SEARCH_INDEX, "test_vs_index")
        self.assertEqual(config.DEPLOYED_INDEX_ID, "test_vs_deployed_id")
        self.assertEqual(config.INDEX_ENDPOINT_ID, "test_vs_endpoint_id")
        self.assertEqual(config.GEMINI_MODEL_ID, "test_gemini")
        self.assertEqual(config.MULTIMODAL_EMBEDDING_MODEL, "test_mm_emb")

    @patch.dict(os.environ, {
        # PROJECT_ID is missing
        "LOCATION": "test_location",
        "BUCKET_NAME": "test_bucket",
        "VECTOR_STORE": "VECTOR_SEARCH",
        **vector_search_specific_vars
    }, clear=True)
    def test_missing_critical_variable(self):
        """Test ValueError is raised if a critical variable (PROJECT_ID) is missing."""
        with self.assertRaisesRegex(ValueError, "Missing critical environment variables: PROJECT_ID"):
            importlib.reload(config)

    @patch.dict(os.environ, {
        **common_critical_vars,
        "VECTOR_STORE": "VECTOR_SEARCH",
        # VECTOR_SEARCH_INDEX is missing
        "DEPLOYED_INDEX_ID": "test_vs_deployed_id",
        "INDEX_ENDPOINT_ID": "test_vs_endpoint_id",
    }, clear=True)
    def test_vector_search_missing_specific_var(self):
        """Test ValueError for VECTOR_STORE=VECTOR_SEARCH if VECTOR_SEARCH_INDEX is missing."""
        with self.assertRaisesRegex(ValueError, "Missing VECTOR_SEARCH specific environment variables: VECTOR_SEARCH_INDEX"):
            importlib.reload(config)

    @patch.dict(os.environ, {
        **common_critical_vars,
        "VECTOR_STORE": "CHROMADB",
        # CHROMADB_COLLECTION_NAME is missing
    }, clear=True)
    def test_chromadb_missing_specific_var(self):
        """Test ValueError for VECTOR_STORE=CHROMADB if CHROMADB_COLLECTION_NAME is missing."""
        with self.assertRaisesRegex(ValueError, "Missing CHROMADB specific environment variable: CHROMADB_COLLECTION_NAME"):
            importlib.reload(config)

    @patch.dict(os.environ, {
        **common_critical_vars,
        "VECTOR_STORE": "INVALID_STORE",
    }, clear=True)
    def test_invalid_vector_store_value(self):
        """Test ValueError is raised for an invalid VECTOR_STORE value."""
        with self.assertRaisesRegex(ValueError, "Unknown VECTOR_STORE value: 'INVALID_STORE'"):
            importlib.reload(config)

    @patch.dict(os.environ, {
        **common_critical_vars,
        "VECTOR_STORE": "CHROMADB",
        **chromadb_specific_vars
    }, clear=True)
    def test_successful_load_chromadb(self):
        """Test successful loading with VECTOR_STORE=CHROMADB and all required vars."""
        importlib.reload(config)
        self.assertEqual(config.PROJECT_ID, "test_project")
        self.assertEqual(config.LOCATION, "test_location")
        self.assertEqual(config.BUCKET_NAME, "test_bucket")
        self.assertEqual(config.VECTOR_STORE, "CHROMADB")
        self.assertEqual(config.CHROMADB_COLLECTION_NAME, "test_chroma_collection")
        # Check that vector search specific vars are None or not set to error values
        self.assertIsNone(config.VECTOR_SEARCH_INDEX)
        self.assertIsNone(config.DEPLOYED_INDEX_ID)
        self.assertIsNone(config.INDEX_ENDPOINT_ID)

    @patch.dict(os.environ, {}, clear=True) # No environment variables set
    def test_all_critical_missing(self):
        """Test ValueError is raised if all critical variables are missing."""
        # This will list multiple missing variables
        with self.assertRaisesRegex(ValueError, "Missing critical environment variables: PROJECT_ID, LOCATION, BUCKET_NAME, VECTOR_STORE"):
            importlib.reload(config)

if __name__ == '__main__':
    unittest.main()
