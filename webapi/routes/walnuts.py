# webapi/routes/walnuts.py
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from pathlib import Path

from common.di_container import Container
from application_layer.commands.command_dispatcher import ICommandDispatcher
from application_layer.queries.walnut__query import IWalnutQuery
from application_layer.commands.command_objects.walnut_command import (
    CreateFakeWalnutCommand,
)
from application_layer.dtos.walnut__dto import WalnutDTO, WalnutImageDTO

router = APIRouter(prefix="/walnuts", tags=["walnuts"])

container = Container()
container.config_path.from_value(str(Path(__file__).resolve().parent.parent.parent / "config.yml"))


def get_command_dispatcher() -> ICommandDispatcher:
    return container.command_dispatcher()


def get_walnut_query() -> IWalnutQuery:
    return container.walnutquery()


class WalnutImageResponse(BaseModel):
    image_id: int
    walnut_id: str
    side: str
    image_path: str
    width: int
    height: int
    checksum: str
    embedding_id: int | None = None


class WalnutResponse(BaseModel):
    walnut_id: str
    description: str
    created_at: str
    created_by: str
    updated_at: str
    updated_by: str
    images: List[WalnutImageResponse]


def _dto_to_response(dto: WalnutDTO) -> WalnutResponse:
    return WalnutResponse(
        walnut_id=dto.walnut_id,
        description=dto.description,
        created_at=dto.created_at.isoformat(),
        created_by=dto.created_by,
        updated_at=dto.updated_at.isoformat(),
        updated_by=dto.updated_by,
        images=[
            WalnutImageResponse(
                image_id=img.image_id,
                walnut_id=img.walnut_id,
                side=img.side,
                image_path=img.image_path,
                width=img.width,
                height=img.height,
                checksum=img.checksum,
                embedding_id=img.embedding_id,
            )
            for img in dto.images
        ],
    )


@router.get("/", response_model=List[WalnutResponse])
async def get_walnuts(
    query: IWalnutQuery = Depends(get_walnut_query)
) -> List[WalnutResponse]:
    walnuts = query.get_all()
    return [_dto_to_response(w) for w in walnuts]


@router.get("/{walnut_id}", response_model=WalnutResponse)
async def get_walnut(
    walnut_id: str,
    query: IWalnutQuery = Depends(get_walnut_query)
) -> WalnutResponse:
    walnut = query.get_by_id(walnut_id)
    if walnut is None:
        raise HTTPException(status_code=404, detail=f"Walnut {walnut_id} not found")
    return _dto_to_response(walnut)


@router.get("/{walnut_id}/load-from-filesystem", response_model=WalnutResponse)
async def load_walnut_from_filesystem(
    walnut_id: str,
    query: IWalnutQuery = Depends(get_walnut_query)
) -> WalnutResponse:
    walnut = query.load_from_filesystem(walnut_id)
    if walnut is None:
        raise HTTPException(status_code=404, detail=f"Walnut {walnut_id} not found in filesystem")
    return _dto_to_response(walnut)


@router.post("/{walnut_id}/create-fake")
async def create_fake_walnut(
    walnut_id: str,
    command_dispatcher: ICommandDispatcher = Depends(get_command_dispatcher)
) -> dict:
    command = CreateFakeWalnutCommand(walnut_id=walnut_id)
    command_dispatcher.dispatch(command)
    return {"message": f"Fake walnut {walnut_id} created"}
