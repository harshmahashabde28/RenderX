"""Native-resolution responsive layout engine: Rows, Columns, Grids, and Flex containers."""
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Tuple, Optional
import pygame

Point2D = Tuple[int, int]


class Align(str, Enum):
    START = "start"
    CENTER = "center"
    END = "end"
    SPACE_BETWEEN = "space_between"


@dataclass
class Rect:
    x: int = 0
    y: int = 0
    w: int = 0
    h: int = 0

    @property
    def left(self) -> int:
        return self.x

    @property
    def top(self) -> int:
        return self.y

    @property
    def right(self) -> int:
        return self.x + self.w

    @property
    def bottom(self) -> int:
        return self.y + self.h

    @property
    def center(self) -> Point2D:
        return (self.x + self.w // 2, self.y + self.h // 2)

    def collidepoint(self, point: Point2D | Tuple[float, float]) -> bool:
        px, py = point
        return self.x <= px <= self.x + self.w and self.y <= py <= self.y + self.h

    def to_pygame_rect(self) -> pygame.Rect:
        return pygame.Rect(self.x, self.y, self.w, self.h)


@dataclass
class Box:
    x: int = 0
    y: int = 0
    width: int = 0
    height: int = 0
    padding: int = 0
    margin: int = 0

    @property
    def inner_rect(self) -> Rect:
        return Rect(
            self.x + self.padding,
            self.y + self.padding,
            max(0, self.width - 2 * self.padding),
            max(0, self.height - 2 * self.padding),
        )

    @property
    def outer_rect(self) -> Rect:
        return Rect(self.x, self.y, self.width, self.height)


class Column:
    """Vertical flex layout."""

    def __init__(
        self,
        x: int,
        y: int,
        width: int,
        spacing: int = 8,
        align: Align = Align.START,
    ):
        self.x = x
        self.y = y
        self.width = width
        self.spacing = spacing
        self.align = align
        self.current_y = y
        self.items: list[Rect] = []

    def add(self, width: int, height: int) -> Rect:
        item_w = min(width, self.width)
        if self.align == Align.CENTER:
            item_x = self.x + (self.width - item_w) // 2
        elif self.align == Align.END:
            item_x = self.x + self.width - item_w
        else:
            item_x = self.x

        rect = Rect(item_x, self.current_y, item_w, height)
        self.items.append(rect)
        self.current_y += height + self.spacing
        return rect

    @property
    def total_height(self) -> int:
        return max(0, self.current_y - self.y - self.spacing)


class Row:
    """Horizontal flex layout."""

    def __init__(
        self,
        x: int,
        y: int,
        height: int,
        spacing: int = 8,
        align: Align = Align.START,
    ):
        self.x = x
        self.y = y
        self.height = height
        self.spacing = spacing
        self.align = align
        self.current_x = x
        self.items: list[Rect] = []

    def add(self, width: int, height: int) -> Rect:
        item_h = min(height, self.height)
        if self.align == Align.CENTER:
            item_y = self.y + (self.height - item_h) // 2
        elif self.align == Align.END:
            item_y = self.y + self.height - item_h
        else:
            item_y = self.y

        rect = Rect(self.current_x, item_y, width, item_h)
        self.items.append(rect)
        self.current_x += width + self.spacing
        return rect

    @property
    def total_width(self) -> int:
        return max(0, self.current_x - self.x - self.spacing)


class Grid:
    """2D uniform grid layout."""

    def __init__(
        self,
        x: int,
        y: int,
        columns: int,
        cell_width: int,
        cell_height: int,
        spacing_x: int = 8,
        spacing_y: int = 8,
    ):
        self.x = x
        self.y = y
        self.columns = max(1, columns)
        self.cell_width = cell_width
        self.cell_height = cell_height
        self.spacing_x = spacing_x
        self.spacing_y = spacing_y
        self.count = 0

    def add(self) -> Rect:
        col = self.count % self.columns
        row = self.count // self.columns
        item_x = self.x + col * (self.cell_width + self.spacing_x)
        item_y = self.y + row * (self.cell_height + self.spacing_y)
        self.count += 1
        return Rect(item_x, item_y, self.cell_width, self.cell_height)
