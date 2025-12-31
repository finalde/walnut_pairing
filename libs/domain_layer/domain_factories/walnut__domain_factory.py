# domain_layer/domain_factories/walnut__domain_factory.py
from typing import Dict, Optional

import numpy as np
from common.either import Either, Left
from common.enums import WalnutSideEnum
from domain_layer.domain_error import DomainError, MissingSideError
from domain_layer.entities.walnut__entity import WalnutEntity
from domain_layer.value_objects.walnut_image__value_object import WalnutImageValueObject


class WalnutDomainFactory:
    @staticmethod
    def create_from_images(images: Dict[str, WalnutImageValueObject], walnut_id: Optional[str] = None) -> Either[WalnutEntity, DomainError]:
        required_sides = {side_enum.value for side_enum in WalnutSideEnum}
        provided_sides = set(images.keys())
        missing_sides = required_sides - provided_sides

        if missing_sides:
            return Left(MissingSideError(list(missing_sides)))

        side_mapping = {
            WalnutSideEnum.FRONT.value: WalnutSideEnum.FRONT,
            WalnutSideEnum.BACK.value: WalnutSideEnum.BACK,
            WalnutSideEnum.LEFT.value: WalnutSideEnum.LEFT,
            WalnutSideEnum.RIGHT.value: WalnutSideEnum.RIGHT,
            WalnutSideEnum.TOP.value: WalnutSideEnum.TOP,
            WalnutSideEnum.DOWN.value: WalnutSideEnum.DOWN,
        }

        image_vos = {}
        for side_str, side_enum in side_mapping.items():
            if side_str not in images:
                return Left(MissingSideError([side_str]))
            image_vos[side_enum.value] = images[side_str]

        return WalnutEntity.create(
            front=image_vos[WalnutSideEnum.FRONT.value],
            back=image_vos[WalnutSideEnum.BACK.value],
            left=image_vos[WalnutSideEnum.LEFT.value],
            right=image_vos[WalnutSideEnum.RIGHT.value],
            top=image_vos[WalnutSideEnum.TOP.value],
            down=image_vos[WalnutSideEnum.DOWN.value],
            walnut_id=walnut_id,
        )

    @staticmethod
    def create_from_file_dao_images(images_by_side: Dict[WalnutSideEnum, WalnutImageValueObject], walnut_id: Optional[str] = None) -> Either[WalnutEntity, DomainError]:
        return WalnutEntity.create(
            front=images_by_side[WalnutSideEnum.FRONT],
            back=images_by_side[WalnutSideEnum.BACK],
            left=images_by_side[WalnutSideEnum.LEFT],
            right=images_by_side[WalnutSideEnum.RIGHT],
            top=images_by_side[WalnutSideEnum.TOP],
            down=images_by_side[WalnutSideEnum.DOWN],
            walnut_id=walnut_id,
        )
