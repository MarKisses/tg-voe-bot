import re
from typing import Self

from pydantic import BaseModel, ValidationError, computed_field


class ItemBase(BaseModel):
    name: str
    id: int

    @classmethod
    def from_api(cls, data: dict | None) -> Self:
        if data is None:
            raise ValidationError

        name = data.get("value", "").replace("..", ".")

        label = data["label"]
        match = re.search(r'data-id="(\d+)"', label)

        if match:
            id = int(match.group(1))
            return cls(name=name, id=id)
        raise ValidationError("Invalid API response format")


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
