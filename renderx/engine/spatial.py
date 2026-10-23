"""Spatial partitioning grid for fast 2D/3D dungeon and entity culling."""
from math import floor, sqrt
from typing import Generic, TypeVar, Set, Tuple

T = TypeVar("T")


class SpatialGrid(Generic[T]):
    """2D uniform grid partitioning objects across the XZ world plane."""

    def __init__(self, cell_size: float = 4.0):
        self.cell_size = float(cell_size)
        self.cells: dict[Tuple[int, int], list[T]] = {}

    def _cell_coords(self, x: float, z: float) -> Tuple[int, int]:
        return (floor(x / self.cell_size), floor(z / self.cell_size))

    def clear(self) -> None:
        self.cells.clear()

    def insert(self, item: T, xmin: float, zmin: float, xmax: float, zmax: float) -> None:
        min_cx, min_cz = self._cell_coords(xmin, zmin)
        max_cx, max_cz = self._cell_coords(xmax, zmax)

        for cx in range(min_cx, max_cx + 1):
            for cz in range(min_cz, max_cz + 1):
                key = (cx, cz)
                if key not in self.cells:
                    self.cells[key] = []
                self.cells[key].append(item)

    def query_radius(self, x: float, z: float, radius: float) -> Set[T]:
        """Retrieve all items occupying cells overlapping a sphere of given radius."""
        min_cx, min_cz = self._cell_coords(x - radius, z - radius)
        max_cx, max_cz = self._cell_coords(x + radius, z + radius)

        results: set[T] = set()
        for cx in range(min_cx, max_cx + 1):
            for cz in range(min_cz, max_cz + 1):
                cell = self.cells.get((cx, cz))
                if cell:
                    results.update(cell)
        return results

    def query_box(self, xmin: float, zmin: float, xmax: float, zmax: float) -> Set[T]:
        """Retrieve all items within an axis-aligned bounding area."""
        min_cx, min_cz = self._cell_coords(xmin, zmin)
        max_cx, max_cz = self._cell_coords(xmax, zmax)

        results: set[T] = set()
        for cx in range(min_cx, max_cx + 1):
            for cz in range(min_cz, max_cz + 1):
                cell = self.cells.get((cx, cz))
                if cell:
                    results.update(cell)
        return results
