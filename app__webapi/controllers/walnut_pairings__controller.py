# app__webapi/controllers/walnut_pairings__controller.py
"""Walnut pairing API controller."""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from application_layer.dtos.walnut_comparison__dto import WalnutComparisonDTO
from application_layer.queries.walnut_comparison__query import IWalnutComparisonQuery
from app__webapi.dependencies import get_walnut_comparison_query
from app__webapi.routes import (
    WALNUT_PAIRINGS_BASE,
    WALNUT_PAIRINGS_BY_WALNUT,
    WALNUT_PAIRINGS_LIST,
    WALNUT_PAIRINGS_SPECIFIC,
)

router = APIRouter(tags=["walnut-pairings"])


@router.get(
    WALNUT_PAIRINGS_LIST,
    response_model=List[WalnutComparisonDTO],
    summary="Get all walnut pairings",
    description="Returns a list of all walnut pairing results, ordered by similarity score (highest first).",
)
async def get_all_pairings_async(
    query: IWalnutComparisonQuery = Depends(get_walnut_comparison_query),
    limit: Optional[int] = Query(None, ge=1, le=1000, description="Maximum number of results to return"),
    offset: Optional[int] = Query(0, ge=0, description="Number of results to skip"),
) -> List[WalnutComparisonDTO]:
    """
    Get all walnut pairing results.
    
    Returns all pairing results sorted by final similarity score (highest first).
    Supports pagination with limit and offset parameters.
    """
    pairings = await query.get_all_pairings_async()
    
    # Apply pagination if specified
    if offset is not None:
        pairings = pairings[offset:]
    if limit is not None:
        pairings = pairings[:limit]
    
    return pairings


@router.get(
    WALNUT_PAIRINGS_BY_WALNUT,
    response_model=List[WalnutComparisonDTO],
    summary="Get pairings for a specific walnut",
    description="Returns all pairing results for a specific walnut, ordered by similarity score.",
)
async def get_pairings_by_walnut_id_async(
    walnut_id: str,
    query: IWalnutComparisonQuery = Depends(get_walnut_comparison_query),
) -> List[WalnutComparisonDTO]:
    """
    Get all pairing results for a specific walnut.
    
    Returns all comparisons where the specified walnut is either the primary
    or compared walnut, sorted by final similarity score (highest first).
    """
    return await query.get_pairings_by_walnut_id_async(walnut_id)


@router.get(
    WALNUT_PAIRINGS_SPECIFIC,
    response_model=WalnutComparisonDTO,
    summary="Get specific pairing",
    description="Returns the pairing result between two specific walnuts.",
)
async def get_pairing_async(
    walnut_id: str,
    compared_walnut_id: str,
    query: IWalnutComparisonQuery = Depends(get_walnut_comparison_query),
) -> WalnutComparisonDTO:
    """
    Get a specific pairing between two walnuts.
    
    Returns the comparison result between the two specified walnuts.
    """
    pairing = await query.get_pairing_async(walnut_id, compared_walnut_id)
    if pairing is None:
        raise HTTPException(
            status_code=404,
            detail=f"Pairing not found between walnut {walnut_id} and {compared_walnut_id}",
        )
    return pairing
