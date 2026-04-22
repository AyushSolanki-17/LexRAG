"""Similarity math utilities for semantic chunking.

This module provides the SimilarityEngine class which implements vector
similarity calculations used in semantic chunking to determine content
coherence and optimal chunk boundaries.
"""

from __future__ import annotations

import math


class SimilarityEngine:
    """Similarity math utilities used during semantic chunking.
    
    This class provides vector similarity calculations that are essential
    for semantic chunking algorithms. It computes cosine similarity between
    embedding vectors to determine content coherence and make intelligent
    decisions about chunk boundaries.
    
    The engine is optimized for performance and numerical stability,
    handling edge cases like zero-length vectors appropriately.
    
    Key features:
        - Cosine similarity calculation for dense vectors
        - Numerical stability handling for edge cases
        - Optimized calculations for chunking workflows
        - Safe handling of zero-length vectors
    """

    def cosine_similarity(self, lhs: list[float], rhs: list[float]) -> float:
        """Computes cosine similarity between two dense vectors.
        
        This method calculates the cosine similarity between two embedding
        vectors, which measures the cosine of the angle between them.
        The result ranges from -1.0 (opposite direction) to 1.0 (same
        direction), with 0.0 indicating orthogonality.
        
        Args:
            lhs: First dense vector (list of float values).
            rhs: Second dense vector (list of float values).
                
        Returns:
            Cosine similarity score between 0.0 and 1.0.
            Returns 0.0 if either vector is zero-length to avoid
            division by zero errors.
            
        Note:
            The method handles vectors of different lengths by using
            zip() without strict mode, which only compares overlapping
            elements. This provides robustness for edge cases.
        """
        dot = sum(lhs_value * rhs_value for lhs_value, rhs_value in zip(lhs, rhs, strict=False))
        lhs_norm = math.sqrt(sum(value * value for value in lhs))
        rhs_norm = math.sqrt(sum(value * value for value in rhs))
        if lhs_norm == 0.0 or rhs_norm == 0.0:
            return 0.0
        return dot / (lhs_norm * rhs_norm)
