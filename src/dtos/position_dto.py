from typing import List

from models import Position


class PositionDTO:
    @staticmethod
    def obj_to_dict(position: Position) -> dict:
        dto = dict()
        dto["position_key"] = position.position_key
        dto["name"] = position.name
        dto["salary_amount"] = position.salary_amount

        return dto

    @staticmethod
    def list_obj_to_list_dict(positions_list: List[Position]) -> List[dict]:
        positions_dict_list = []

        for position in positions_list:
            positions_dict_list.append(PositionDTO.obj_to_dict(position))

        return positions_dict_list

    @staticmethod
    def only_obj_key(position: Position) -> dict:
        dto = dict()
        dto["position_key"] = position.position_key

        return dto
