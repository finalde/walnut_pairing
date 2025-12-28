# webapi/routes/walnuts.py
"""Walnut API routes."""
from fastapi import APIRouter, Depends, HTTPException
from typing import List
from pydantic import BaseModel
import sys
from pathlib import Path

# Add libs to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "libs"))

from webapi.dependencies import get_container
from src.application_layer.walnut__al import IWalnutAL
from src.infrastructure_layer.data_access_objects import WalnutDBDAO

router = APIRouter()


class WalnutResponse(BaseModel):
    """Walnut response model."""
    id: str
    description: str
    image_count: int

    class Config:
        from_attributes = True


def get_walnut_al() -> IWalnutAL:
    """Dependency to get WalnutAL from container."""
    container = get_container()
    return container.walnut_al()


@router.get("/walnuts", response_model=List[WalnutResponse])
async def get_walnuts(walnut_al: IWalnutAL = Depends(get_walnut_al)) -> List[WalnutResponse]:
    """Get all walnuts."""
    try:
        walnuts = walnut_al.walnut_reader.get_all()
        return [
            WalnutResponse(
                id=w.id,
                description=w.description,
                image_count=len(w.images)
            )
            for w in walnuts
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/walnuts/{walnut_id}", response_model=WalnutResponse)
async def get_walnut(
    walnut_id: str,
    walnut_al: IWalnutAL = Depends(get_walnut_al)
) -> WalnutResponse:
    """Get a walnut by ID."""
    try:
        walnut = walnut_al.walnut_reader.get_by_id(walnut_id)
        if not walnut:
            raise HTTPException(status_code=404, detail=f"Walnut {walnut_id} not found")
        return WalnutResponse(
            id=walnut.id,
            description=walnut.description,
            image_count=len(walnut.images)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/walnuts/{walnut_id}/load-from-filesystem")
async def load_walnut_from_filesystem(
    walnut_id: str,
    walnut_al: IWalnutAL = Depends(get_walnut_al)
) -> WalnutResponse:
    """Load a walnut from filesystem and save to database."""
    try:
        walnut = walnut_al.load_and_save_walnut_from_filesystem(walnut_id)
        return WalnutResponse(
            id=walnut.id,
            description=walnut.description,
            image_count=len(walnut.images)
        )
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
