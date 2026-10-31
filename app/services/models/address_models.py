import re
from typing import Self

from pydantic import BaseModel, computed_field


class ItemBase(BaseModel):
    name: str
    id: int

    @classmethod
    def from_api(cls, data: dict) -> Self:
        # New API format: {"id": "510100000", "label": "м.Вінниця (Вінницька Область/М.Вінниця)"}
        return cls(id=int(data["id"]), name=data["label"].strip())


class City(ItemBase): ...


class Street(ItemBase): ...


class House(ItemBase): ...


class Address(BaseModel):
    city: City
    street: Street
    house: House

    @computed_field
    @property
    def id(self) -> str:
        return f"{self.city.id}-{self.street.id}-{self.house.id}"

    @computed_field
    @property
    def name(self) -> str:
        match = re.search(r'(.+)\s\(', self.city.name)
        if match:
            return f"{match.group(1)}, {self.street.name}, {self.house.name}"
        return f"{self.city.name[:10]}, {self.street.name}, {self.house.name}"
