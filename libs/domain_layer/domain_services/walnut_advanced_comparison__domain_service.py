# domain_layer/domain_services/walnut_advanced_comparison__domain_service.py
from typing import Dict, Optional

import numpy as np
from common.enums import WalnutSideEnum
from domain_layer.value_objects.walnut_image__value_object import WalnutImageValueObject


class WalnutAdvancedComparisonDomainService:
    """
    Domain service for advanced walnut comparison using embeddings.
    
    Contains business rules about how walnuts are compared using embeddings
    and how similarity scores are calculated with side-specific weights.
    """

    @staticmethod
    def cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
        """
        Calculate cosine similarity between two vectors.
        
        Args:
            vec1: First vector (embedding)
            vec2: Second vector (embedding)
        
        Returns:
            Cosine similarity score between 0 and 1 (1 = identical, 0 = orthogonal)
        """
        # Normalize vectors
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        # Handle zero vectors
        if norm1 == 0.0 or norm2 == 0.0:
            return 0.0
        
        # Calculate cosine similarity
        dot_product = np.dot(vec1, vec2)
        cosine_sim = dot_product / (norm1 * norm2)
        
        # Cosine similarity ranges from -1 to 1, normalize to 0-1 range
        # (1 + cosine_sim) / 2 maps [-1, 1] to [0, 1]
        normalized_similarity = (cosine_sim + 1.0) / 2.0
        
        return float(normalized_similarity)

    @staticmethod
    def compare_side_embeddings(
        image1: Optional[WalnutImageValueObject],
        image2: Optional[WalnutImageValueObject],
    ) -> float:
        """
        Compare embeddings of two images from the same side.
        
        Args:
            image1: First walnut's image value object (can be None)
            image2: Second walnut's image value object (can be None)
        
        Returns:
            Similarity score between 0 and 1 (0 if either image is missing or has no embedding)
        """
        # If either image is missing, return 0
        if image1 is None or image2 is None:
            return 0.0
        
        # Ensure both images have embeddings
        if image1.embedding.size == 0 or image2.embedding.size == 0:
            return 0.0
        
        # Ensure embeddings have the same shape
        if image1.embedding.shape != image2.embedding.shape:
            return 0.0
        
        return WalnutAdvancedComparisonDomainService.cosine_similarity(
            image1.embedding, image2.embedding
        )

    @staticmethod
    def calculate_advanced_similarity(
        walnut1_images: Dict[WalnutSideEnum, WalnutImageValueObject],
        walnut2_images: Dict[WalnutSideEnum, WalnutImageValueObject],
        front_weight: float,
        back_weight: float,
        left_weight: float,
        right_weight: float,
        top_weight: float,
        down_weight: float,
    ) -> tuple[Dict[WalnutSideEnum, float], float]:
        """
        Calculate advanced similarity between two walnuts using embeddings.
        
        Business rules:
        - Compare embeddings for each side (front, back, left, right, top, down)
        - Calculate side-specific similarity scores using cosine similarity
        - Calculate final weighted similarity score using side weights
        - Final score formula:
          score = (front_sim * front_weight + back_sim * back_weight + 
                   left_sim * left_weight + right_sim * right_weight +
                   top_sim * top_weight + down_sim * down_weight)
        
        Args:
            walnut1_images: Dictionary mapping side to image value object for first walnut
            walnut2_images: Dictionary mapping side to image value object for second walnut
            front_weight: Weight for front side similarity
            back_weight: Weight for back side similarity
            left_weight: Weight for left side similarity
            right_weight: Weight for right side similarity
            top_weight: Weight for top side similarity
            down_weight: Weight for down side similarity
        
        Returns:
            Tuple of (side_similarities dict, final_advanced_similarity)
        """
        # Compare each side
        side_similarities: Dict[WalnutSideEnum, float] = {}
        
        for side_enum in WalnutSideEnum:
            image1 = walnut1_images.get(side_enum)
            image2 = walnut2_images.get(side_enum)
            
            side_similarities[side_enum] = WalnutAdvancedComparisonDomainService.compare_side_embeddings(
                image1, image2
            )
        
        # Calculate weighted final similarity score
        final_score = (
            front_weight * side_similarities[WalnutSideEnum.FRONT] +
            back_weight * side_similarities[WalnutSideEnum.BACK] +
            left_weight * side_similarities[WalnutSideEnum.LEFT] +
            right_weight * side_similarities[WalnutSideEnum.RIGHT] +
            top_weight * side_similarities[WalnutSideEnum.TOP] +
            down_weight * side_similarities[WalnutSideEnum.DOWN]
        )
        
        # Ensure score is between 0 and 1 (clip if necessary)
        final_score = min(max(final_score, 0.0), 1.0)
        
        return side_similarities, final_score

