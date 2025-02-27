import pickle
from dataclasses import dataclass, field
from typing import Generic, Optional

from cortex_ingestion._exceptions import InvalidStorageError
from cortex_ingestion._types import GTBlob
from cortex_ingestion._utils import logger, load_pickle, save_pickle

from cortex_ingestion._storage._base import BaseBlobStorage


@dataclass
class PickleBlobStorage(BaseBlobStorage[GTBlob]):
    """A blob storage that uses pickle to serialize the blob."""

    RESOURCE_NAME = "blob.pkl"
    _blob: Optional[GTBlob] = field(init=False, default=None)

    async def get(self) -> Optional[GTBlob]:
        """Get the blob.

        Returns:
            The blob or None if it doesn't exist.
        """
        return self._blob

    async def set(self, blob: GTBlob) -> None:
        """Set the blob.

        Args:
            blob: The blob to set.
        """
        self._blob = blob

    async def _insert_start(self):
        """Prepare the storage for inserting."""
        # Load the blob if it exists
        self._blob = load_pickle(self.namespace, self.RESOURCE_NAME, None)

    async def _insert_done(self):
        """Commit the storage after inserting."""
        # Save the blob if it exists
        if self._blob is not None:
            save_pickle(self.namespace, self.RESOURCE_NAME, self._blob)

    async def _query_start(self):
        """Prepare the storage for querying."""
        # Load the blob if it exists
        self._blob = load_pickle(self.namespace, self.RESOURCE_NAME, None)

    async def _query_done(self):
        """Release the storage after querying."""
        pass
