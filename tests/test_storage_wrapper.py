import unittest
from unittest.mock import patch, MagicMock, ANY
import os
import json
import importlib

# Assuming config.py is at the root and discoverable.
# We need to ensure config is loaded with test environment variables *before* storage_wrapper imports it,
# especially if storage_wrapper uses config at the module level (e.g., for the global storage instance).
# For testing a fresh Storage() instance, we can set env vars, reload config, then instantiate.

class TestStorage(unittest.TestCase):

    @patch.dict(os.environ, {
        "PROJECT_ID": "test-project",
        "LOCATION": "test-location",
        "BUCKET_NAME": "test-bucket"
    }, clear=True)
    def setUp(self):
        # Reload config to ensure it picks up the mocked environment variables for this test class
        import config
        importlib.reload(config)

        from storage_wrapper import Storage # Import/Reload Storage after config is set
        # If storage_wrapper has a global 'storage = Storage()' instance, it might have already been created
        # with production config. For robust testing, it's better if Storage instances are created
        # explicitly in the code under test, or if the global instance can be easily patched/reloaded.
        # Here, we are testing a new instance of Storage.

        self.storage = Storage(
            project=config.PROJECT_ID,
            location=config.LOCATION,
            bucket_name=config.BUCKET_NAME
        )

        # Mock GCS client and bucket that are attributes of the Storage instance
        self.mock_gcs_client_instance = MagicMock() # This is what storage.Client() would return
        self.mock_bucket_instance = MagicMock()

        # Patch the google.cloud.storage.Client constructor if Storage() creates its own client.
        # If we pass client/bucket instances to Storage, we wouldn't need this.
        # The current Storage class creates its own client. So, we mock at the class level.
        # However, for simplicity here, we are replacing the instance's client and bucket directly.
        self.storage.client = self.mock_gcs_client_instance
        self.storage.bucket = self.mock_bucket_instance

        # Common mock blob
        self.mock_blob = MagicMock()
        self.mock_bucket_instance.blob.return_value = self.mock_blob

        # Ensure cache directory for tests is mocked or controlled
        self.original_cache_dir = self.storage.cache
        self.storage.cache = ".test_cache" # Use a test-specific cache name

        # Keep track of patches to stop them in tearDown
        self.patches = []

        # Patch os.mkdir to prevent actual directory creation during tests
        mkdir_patch = patch("os.mkdir")
        self.mock_mkdir = mkdir_patch.start()
        self.patches.append(mkdir_patch)

    def tearDown(self):
        # Stop all patches started in setUp or tests
        for p in self.patches:
            p.stop()
        # Restore original cache dir if necessary, though Storage instances are per-test method here due to setUp
        # If actual directories were created, clean them up:
        # if os.path.exists(self.storage.cache) and self.storage.cache == ".test_cache":
        #     import shutil
        #     shutil.rmtree(self.storage.cache)
        pass


    def test_write_json_success(self):
        test_data = {"data": "test_value"}
        test_filename = "test_file.json"

        self.storage.write_json(test_data, test_filename)

        self.mock_bucket_instance.blob.assert_called_once_with(test_filename)
        self.mock_blob.upload_from_string.assert_called_once_with(
            data=json.dumps(test_data),
            content_type='application/json'
        )

    def test_read_json_success(self):
        test_filename = "test_read.json"
        expected_data = {"data": "read_value"}
        self.mock_blob.download_as_string.return_value = json.dumps(expected_data)

        result = self.storage.read_json(test_filename)

        self.mock_bucket_instance.blob.assert_called_once_with(test_filename)
        self.mock_blob.download_as_string.assert_called_once()
        self.assertEqual(result, expected_data)

    def test_exists_returns_true(self):
        test_filename = "existing_file.json"
        self.mock_blob.exists.return_value = True

        self.assertTrue(self.storage.exists(test_filename))
        self.mock_bucket_instance.blob.assert_called_once_with(test_filename)
        self.mock_blob.exists.assert_called_once()

    def test_exists_returns_false(self):
        test_filename = "non_existing_file.json"
        self.mock_blob.exists.return_value = False

        self.assertFalse(self.storage.exists(test_filename))
        self.mock_bucket_instance.blob.assert_called_once_with(test_filename)
        self.mock_blob.exists.assert_called_once()

    @patch("os.path.isfile", return_value=False)
    def test_local_file_downloads_if_not_exists(self, mock_isfile):
        # os.mkdir is already patched in setUp
        test_filename = "test_download.mp4"
        expected_local_path = os.path.join(self.storage.cache, test_filename)

        local_path = self.storage.local_file(test_filename)

        mock_isfile.assert_called_once_with(expected_local_path)
        self.mock_bucket_instance.blob.assert_called_once_with(test_filename)
        self.mock_blob.download_to_filename.assert_called_once_with(expected_local_path)
        self.assertEqual(local_path, expected_local_path)

    @patch("os.path.isfile", return_value=True)
    def test_local_file_returns_existing_if_exists(self, mock_isfile):
        # os.mkdir is already patched in setUp
        test_filename = "existing_local.mp4"
        expected_local_path = os.path.join(self.storage.cache, test_filename)

        local_path = self.storage.local_file(test_filename)

        mock_isfile.assert_called_once_with(expected_local_path)
        self.mock_bucket_instance.blob.assert_not_called() # Should not interact with GCS
        self.mock_blob.download_to_filename.assert_not_called()
        self.assertEqual(local_path, expected_local_path)

    def test_list_files_success_no_extension(self):
        mock_blob_1 = MagicMock()
        mock_blob_1.name = "file1.txt"
        mock_blob_2 = MagicMock()
        mock_blob_2.name = "file2.mp4"

        # Configure the bucket's list_blobs method, not the client's
        self.mock_bucket_instance.list_blobs.return_value = [mock_blob_1, mock_blob_2]

        result = self.storage.list_files()

        self.mock_bucket_instance.list_blobs.assert_called_once()
        self.assertEqual(result, ["file1.txt", "file2.mp4"])

    def test_list_files_success_with_extension(self):
        mock_blob_1 = MagicMock()
        mock_blob_1.name = "file1.txt"
        mock_blob_2 = MagicMock()
        mock_blob_2.name = "file2.mp4"
        mock_blob_3 = MagicMock()
        mock_blob_3.name = "another.mp4"

        self.mock_bucket_instance.list_blobs.return_value = [mock_blob_1, mock_blob_2, mock_blob_3]

        result = self.storage.list_files(extension=".mp4")

        self.mock_bucket_instance.list_blobs.assert_called_once()
        self.assertEqual(result, ["file2.mp4", "another.mp4"])

    def test_upload_file_success(self):
        local_path = "local/path/to/file.mp4"
        remote_filename = "remote_uploaded_file.mp4"

        self.storage.upload_file(local_path, remote_filename)

        self.mock_bucket_instance.blob.assert_called_once_with(remote_filename)
        self.mock_blob.upload_from_filename.assert_called_once_with(local_path)

if __name__ == '__main__':
    unittest.main()
