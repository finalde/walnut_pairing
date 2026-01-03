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
    def cosine_similarity(
        vec1: np.ndarray,
        vec2: np.ndarray,
        discriminative_power: float = 2.0,
        min_expected_cosine: float = 0.3,
        max_expected_cosine: float = 0.9,
    ) -> float:
        """
        Calculate cosine similarity between two vectors with discriminative transformation.
        
        Business rule: Apply power transformation to make high scores more rare and meaningful.
        For embeddings (typically normalized and in positive space), cosine similarity usually
        ranges from ~0.3 to ~0.9. We apply a power transformation to spread out the scores
        so that 0.8-0.9 scores truly indicate high-quality matches.
        
        Args:
            vec1: First vector (embedding)
            vec2: Second vector (embedding)
            discriminative_power: Power to apply for transformation (default 2.0)
                                 Higher values make high scores rarer
        
        Returns:
            Cosine similarity score between 0 and 1 (1 = identical, 0 = very different)
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
        
        # For ResNet embeddings, cosine similarity typically ranges from ~0.3 to ~0.9
        # We need to normalize to 0-1 range, but make it more discriminative
        # Strategy: 
        # 1. Shift and scale to map typical range [min_expected, max_expected] to approximately [0, 1]
        # 2. Apply power transformation to make high scores rarer
        
        # First, normalize assuming typical range maps to [0, 1]
        # This means cosine min_expected → 0.0, cosine max_expected → 1.0
        range_size = max_expected_cosine - min_expected_cosine
        
        # Normalize to 0-1 range based on expected distribution
        normalized = (cosine_sim - min_expected_cosine) / range_size
        
        # Clip to [0, 1] range
        normalized = max(0.0, min(1.0, normalized))
        
        # Apply power transformation to make high scores rarer
        # Higher power means high scores are harder to achieve
        # Example: normalized=0.8, power=2.0 → 0.8^2 = 0.64 (lower score)
        # This means only very high cosine similarities will result in high final scores
        discriminative_score = normalized ** discriminative_power
        
        return float(discriminative_score)

    @staticmethod
    def compare_side_embeddings(
        image1: Optional[WalnutImageValueObject],
        image2: Optional[WalnutImageValueObject],
        discriminative_power: float = 2.0,
        min_expected_cosine: float = 0.3,
        max_expected_cosine: float = 0.9,
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
            image1.embedding, image2.embedding, discriminative_power, min_expected_cosine, max_expected_cosine
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
        discriminative_power: float = 2.0,
        min_expected_cosine: float = 0.3,
        max_expected_cosine: float = 0.9,
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
                image1, image2, discriminative_power, min_expected_cosine, max_expected_cosine
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

