import logging
from typing import List, Optional, Tuple

import numpy as np
from scipy.sparse import csr_matrix

from cortex_ingestion._utils._pickle import load_pickle, save_pickle

logger = logging.getLogger("cortex_ingestion")


def csr_from_indices_list(indices_list: List[List[int]], shape: Optional[Tuple[int, int]] = None) -> csr_matrix:
    """Create a CSR matrix from a list of indices.

    Args:
        indices_list: A list of lists of indices.
        shape: The shape of the matrix.

    Returns:
        A CSR matrix.
    """
    if not indices_list:
        return csr_matrix((0, 0))

    if shape is None:
        shape = (len(indices_list), max(max(indices) + 1 for indices in indices_list if indices))

    data = []
    row_ind = []
    col_ind = []

    for i, indices in enumerate(indices_list):
        for j in indices:
            data.append(1)
            row_ind.append(i)
            col_ind.append(j)

    return csr_matrix((data, (row_ind, col_ind)), shape=shape)


__all__ = ["logger", "csr_from_indices_list", "load_pickle", "save_pickle"] 