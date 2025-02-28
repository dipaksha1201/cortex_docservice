import pickle
from typing import Any, Optional

from cortex_ingestion._exceptions import InvalidStorageError
from cortex_ingestion._storage._namespace import Namespace
from cortex_ingestion._utils import logger
from cortex_ingestion.cloud_services._googlecloud import download_pickle_from_gcs, upload_pickle_to_gcs


def load_pickle(namespace: Namespace, resource_name: str, default: Any = None) -> Any:
    """Load a pickle file from the namespace.
    
    Args:
        namespace: The namespace to load from.
        resource_name: The name of the resource to load.
        default: The default value to return if the file doesn't exist.
        
    Returns:
        The loaded data or the default value.
        
    Raises:
        InvalidStorageError: If there's an error loading the file.
    """
    if not namespace:
        return default
        
    file_path = namespace.get_load_path(resource_name)
    if not file_path:
        return default
    
    try:
        data = download_pickle_from_gcs(file_path)
        return data
    except Exception as e:
        error_msg = f"Error loading pickle file {file_path}: {e}"
        logger.error(error_msg)
        raise InvalidStorageError(error_msg) from e


def save_pickle(namespace: Namespace, resource_name: str, data: Any) -> None:
    """Save data to a pickle file in the namespace.
    
    Args:
        namespace: The namespace to save to.
        resource_name: The name of the resource to save.
        data: The data to save.
        
    Raises:
        InvalidStorageError: If there's an error saving the file.
    """
    if not namespace:
        logger.warning("Cannot save pickle data: no namespace provided")
        return
        
    file_path = namespace.get_save_path(resource_name)
    
    try:
        upload_pickle_to_gcs(file_path, data)
        logger.debug(f"Saved pickle data to '{file_path}'")
    except Exception as e:
        error_msg = f"Error saving pickle file {file_path}: {e}"
        logger.error(error_msg)
        raise InvalidStorageError(error_msg) from e 