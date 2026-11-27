from dataclasses import dataclass


@dataclass(frozen=True)
class LineItem:
    """One line: an item (ID in Inventory) and a number of boxes. Shared by trips and assignments."""
    item_id: int
    boxes: int
