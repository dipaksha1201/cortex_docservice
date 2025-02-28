import io
from google.cloud import storage
import pickle
from google.api_core import exceptions as google_exceptions
import os
from pathlib import Path
from cortex_ingestion._utils import logger

# from cortex_ingestion._storage._namespace import Namespace
from cortex_ingestion._exceptions import InvalidStorageError

# Get the absolute path to the credentials file relative to this script
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_CREDENTIALS_PATH = os.path.join(SCRIPT_DIR, "cortex-service-key.json")

bucket_name = "cortex-knowledge-base-beta"

def get_authenticated_storage_client(credentials_path=DEFAULT_CREDENTIALS_PATH):
    """
    Returns an authenticated Google Cloud Storage client using service account credentials.
    """
    try:
        abs_path = os.path.abspath(credentials_path)
        if not os.path.exists(abs_path):
            raise FileNotFoundError(f"Credentials file not found at: {abs_path}")
        return storage.Client.from_service_account_json(abs_path)
    except Exception as e:
        raise InvalidStorageError(f"Failed to authenticate: {str(e)}")

def blob_exists(blob_path: str, bucket_name="cortex-knowledge-base-beta") -> bool:
    """
    Check if a blob exists in the GCS bucket
    
    Args:
        blob_path: Path to the blob in the bucket
        bucket_name: Name of the GCS bucket (optional)
            
    Returns:
        bool: True if blob exists, False otherwise
    """
    try:
        # If checking a directory and path doesn't end with slash, append it
        # if not blob_path.endswith('/') and '.' not in blob_path.split('/')[-1]:
        #     blob_path += '/'
            
        client = get_authenticated_storage_client()
        bucket = client.bucket(bucket_name)
        # Ensure the folder path ends with '/'
        if not blob_path.endswith('/'):
            blob_path += '/'

        blobs = list(bucket.list_blobs(prefix=blob_path, max_results=1))  
        return len(blobs) > 0
        # return blob.exists()
    except google_exceptions.Forbidden as e:
        raise InvalidStorageError(f"Authentication failed or insufficient permissions: {str(e)}")
    except Exception as e:
        # raise e
        raise InvalidStorageError(f"Failed to check blob existence: {str(e)}")
    
def list_blobs(prefix: str = "", delimiter: str = "/", bucket_name: str = "cortex-knowledge-base-beta") -> list[str]:
    """
    List all blob paths under the specified prefix
    
    Args:
        prefix: The prefix path to list objects from (default empty string for root)
        delimiter: Delimiter to use for hierarchy (default '/')
        bucket_name: Name of the GCS bucket (optional)
    
    Returns:
        list[str]: List of blob paths under the prefix
        
    Raises:
        InvalidStorageError: If listing fails due to permissions or other issues
    """
    try:
        client = get_authenticated_storage_client()
        bucket = client.bucket(bucket_name)
        
        # List all blobs with the prefix
        blobs = bucket.list_blobs(prefix=prefix, delimiter=delimiter)
        
        # Get both direct blobs and prefixes (folders)
        paths = []
        
        # Add direct blob paths
        for blob in blobs:
            paths.append(blob.name)
            
        return sorted(paths)
    except google_exceptions.Forbidden as e:
        raise InvalidStorageError(f"Authentication failed or insufficient permissions: {str(e)}")
    except Exception as e:
        raise InvalidStorageError(f"Failed to list blobs: {str(e)}")

def delete_blob(blob_path: str, bucket_name: str = "cortex-knowledge-base-beta") -> None:
    """
    Delete a blob from the GCS bucket
    
    Args:
        blob_path: Path to the blob to delete
        bucket_name: Name of the GCS bucket (optional)
    
    Raises:
        InvalidStorageError: If deletion fails due to permissions or other issues
    """
    try:
        client = get_authenticated_storage_client()
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(blob_path)
        
        if not blob.exists():
            logger.info(f"Blob does not exist at path: {blob_path}")
            return
            
        blob.delete()
        logger.info(f"Successfully deleted blob at gs://{bucket_name}/{blob_path}")
    except google_exceptions.Forbidden as e:
        raise InvalidStorageError(f"Authentication failed or insufficient permissions: {str(e)}")
    except Exception as e:
        raise InvalidStorageError(f"Failed to delete blob: {str(e)}")

def create_directory(dir_path: str, bucket_name: str = "cortex-knowledge-base-beta") -> None:
    """
    Create a directory marker in GCS (empty blob with trailing slash)
    
    Args:
        dir_path: Path where the directory should be created
        bucket_name: Name of the GCS bucket (optional)
    """
    if not dir_path.endswith('/'):
        dir_path += '/'
        
    try:
        client = get_authenticated_storage_client()
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(dir_path)
        
        if not blob.exists():
            blob.upload_from_string('')
            logger.info(f"Created directory marker at gs://{bucket_name}/{dir_path}")
    except Exception as e:
        logger.warning(f"Failed to create directory marker: {str(e)}")

def rename_blob(old_path: str, new_path: str, bucket_name: str = "cortex-knowledge-base-beta") -> None:
    """
    Rename (move) a blob to a new path in the GCS bucket
    
    Args:
        old_path: Current path of the blob
        new_path: New path for the blob
        bucket_name: Name of the GCS bucket (optional)
    
    Raises:
        InvalidStorageError: If rename fails due to permissions or other issues
    """
    try:
        client = get_authenticated_storage_client()
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(old_path)
        
        if not blob.exists():
            logger.info(f"Source blob does not exist at path: {old_path}")
            return
            
        new_blob = bucket.copy_blob(blob, bucket, new_path)
        blob.delete()
        logger.info(f"Successfully renamed blob from gs://{bucket_name}/{old_path} to gs://{bucket_name}/{new_path}")
    except google_exceptions.Forbidden as e:
        raise InvalidStorageError(f"Authentication failed or insufficient permissions: {str(e)}")
    except Exception as e:
        raise InvalidStorageError(f"Failed to rename blob: {str(e)}")

def upload_pickle_to_gcs(blobpath, data, credentials_path=DEFAULT_CREDENTIALS_PATH, bucket_name=bucket_name):
    """Pickles the data and uploads it to the specified GCS bucket/path."""
    try:
        client = get_authenticated_storage_client(credentials_path)
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(blobpath)
        
        # Serialize data
        pickle_data = pickle.dumps(data)
        
        # Upload the serialized data
        blob.upload_from_string(pickle_data)
        print(f"Data successfully uploaded to gs://{bucket_name}/{blobpath}")
    except google_exceptions.Forbidden as e:
        raise InvalidStorageError(f"Authentication failed or insufficient permissions: {str(e)}")
    except google_exceptions.NotFound as e:
        raise InvalidStorageError(f"Bucket {bucket_name} not found: {str(e)}")
    except pickle.PickleError as e:
        raise InvalidStorageError(f"Failed to serialize data: {str(e)}")
    except Exception as e:
        raise InvalidStorageError(f"Failed to upload data to storage: {str(e)}")

def upload_graph_to_gcs(blobpath, buffer, credentials_path=DEFAULT_CREDENTIALS_PATH, bucket_name=bucket_name):
    """Uploads the graph data to the specified GCS bucket/path."""
    try:
        client = get_authenticated_storage_client(credentials_path)
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(blobpath)
        
        # Upload the serialized data
        blob.upload_from_file(buffer)
        print(f"Graph successfully uploaded to gs://{bucket_name}/{blobpath}")
    except google_exceptions.Forbidden as e:
        raise InvalidStorageError(f"Authentication failed or insufficient permissions: {str(e)}")
    except google_exceptions.NotFound as e:
        raise InvalidStorageError(f"Bucket {bucket_name} not found: {str(e)}")
    except pickle.PickleError as e:
        raise InvalidStorageError(f"Failed to serialize data: {str(e)}")
    except Exception as e:
        raise InvalidStorageError(f"Failed to upload data to storage: {str(e)}")
    
def download_graph_to_gcs(blobpath, credentials_path=DEFAULT_CREDENTIALS_PATH, bucket_name=bucket_name):
    """Uploads the graph data to the specified GCS bucket/path."""
    try:
        client = get_authenticated_storage_client(credentials_path)
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(blobpath)
        
        # Upload the serialized data
        buffer = io.BytesIO()
        blob.download_to_file(buffer)
        buffer.seek(0)
        
        print(f"Graph successfully uploaded to gs://{bucket_name}/{blobpath}")
        return buffer
    
    except google_exceptions.Forbidden as e:
        raise InvalidStorageError(f"Authentication failed or insufficient permissions: {str(e)}")
    except google_exceptions.NotFound as e:
        raise InvalidStorageError(f"Bucket {bucket_name} not found: {str(e)}")
    except pickle.PickleError as e:
        raise InvalidStorageError(f"Failed to serialize data: {str(e)}")
    except Exception as e:
        raise InvalidStorageError(f"Failed to upload data to storage: {str(e)}")
    
def download_pickle_from_gcs(blobpath, credentials_path=DEFAULT_CREDENTIALS_PATH, bucket_name=bucket_name):
    """Downloads the pickled data from the specified GCS bucket/path and unpickles it."""
    try:
        client = get_authenticated_storage_client(credentials_path)
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(blobpath)
        
        # Download and deserialize the data
        pickle_data = blob.download_as_string()
        data = pickle.loads(pickle_data)
        print(f"Data successfully downloaded from gs://{bucket_name}/{blobpath}")
        return data
    except google_exceptions.Forbidden as e:
        raise InvalidStorageError(f"Authentication failed or insufficient permissions: {str(e)}")
    except google_exceptions.NotFound as e:
        raise InvalidStorageError(f"Resource not found at gs://{bucket_name}/{blobpath}: {str(e)}")
    except pickle.PickleError as e:
        raise InvalidStorageError(f"Failed to deserialize data: {str(e)}")
    except Exception as e:
        raise InvalidStorageError(f"Failed to download data from storage: {str(e)}")


if __name__ == "__main__":
    # Set your bucket name, blob path, and optionally the credentials path
    blob_path = "tmp/"

    # Example data to pickle
    data_to_pickle = {"message": "Hello GCP with authentication!", "numbers": [1, 2, 3]}
    status = blob_exists(blob_path)
    print(status)
    
    # Upload and then download the data
    # upload_pickle_to_gcs(bucket_name, blob_path, data_to_pickle, credentials_path)
    # retrieved_data = download_pickle_from_gcs(bucket_name, blob_path, credentials_path)
    
    # print("Retrieved Data:", retrieved_data)