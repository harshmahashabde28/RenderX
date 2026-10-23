"""Dual-mode camera: supports both fixed orbit/lab projection and 6-DOF first-person view."""
from dataclasses import dataclass, field
from math import cos, sin, pi, isfinite
from typing import Tuple, Optional
from renderx import config
from renderx.core.clipping import clip_edge_near
from renderx.core.projection import project_point, project_orthographic

Point3D = Tuple[float, float, float]
Point2D = Tuple[float, float]


@dataclass
class Camera:
    """Camera supporting world-to-camera transformation and projection.

    Attributes:
        position: (x, y, z) coordinates in world space.
        yaw: Horizontal viewing angle in radians (0 = looking forward along +Z).
        pitch: Vertical tilt in radians (positive = looking down/up).
        roll: Camera roll in radians.
        focal_length: Focal length for perspective projection.
    """
    position: Point3D = (0.0, 0.0, 0.0)
    yaw: float = 0.0
    pitch: float = 0.0
    roll: float = 0.0
    focal_length: float = config.FOCAL_LENGTH

    def to_camera_space(self, world_point: Point3D) -> Point3D:
        """Transform a world coordinate into camera coordinates.

        Applies translation relative to camera position, followed by inverse view rotation
        (yaw, pitch, roll). When yaw, pitch, and roll are 0, this is a pure translation.
        """
        # Translation relative to camera
        x = world_point[0] - self.position[0]
        y = world_point[1] - self.position[1]
        z = world_point[2] - self.position[2]

        if self.yaw == 0.0 and self.pitch == 0.0 and self.roll == 0.0:
            return (x, y, z)

        # Inverse yaw rotation (around world Y)
        cy, sy = cos(-self.yaw), sin(-self.yaw)
        rx = x * cy + z * sy
        rz = -x * sy + z * cy

        # Inverse pitch rotation (around camera X)
        cp, sp = cos(-self.pitch), sin(-self.pitch)
        ry = y * cp - rz * sp
        rz = y * sp + rz * cp

        # Inverse roll rotation (around camera Z) if non-zero
        if self.roll != 0.0:
            cr, sr = cos(-self.roll), sin(-self.roll)
            rrx = rx * cr - ry * sr
            rry = rx * sr + ry * cr
            return (rrx, rry, rz)

        return (rx, ry, rz)

    def relative_point(self, world_point: Point3D) -> Point3D:
        """Backwards-compatible alias for to_camera_space."""
        return self.to_camera_space(world_point)

    def project(
        self,
        world_point: Point3D,
        mode: str = "Perspective",
        *,
        centre: Point2D = config.CENTRE,
        focal_length: Optional[float] = None,
    ) -> Optional[Point2D]:
        """Project a world space point onto 2D screen coordinates."""
        f_len = self.focal_length if focal_length is None else focal_length
        return self.project_relative(
            self.to_camera_space(world_point), mode, centre=centre, focal_length=f_len
        )

    def project_relative(
        self,
        camera_point: Point3D,
        mode: str = "Perspective",
        *,
        centre: Point2D = config.CENTRE,
        focal_length: Optional[float] = None,
    ) -> Optional[Point2D]:
        """Project a camera-space point onto 2D screen coordinates."""
        f_len = self.focal_length if focal_length is None else focal_length
        if mode == "Orthographic":
            return project_orthographic(
                camera_point, centre, f_len / config.DEFAULT_DEPTH
            )
        return project_point(camera_point, centre, f_len)

    def project_edge(
        self,
        world_a: Point3D,
        world_b: Point3D,
        mode: str = "Perspective",
        *,
        centre: Point2D = config.CENTRE,
        focal_length: Optional[float] = None,
    ) -> Optional[Tuple[Point2D, Point2D]]:
        """Clip a 3D world edge against the near plane and project to 2D screen coordinates."""
        f_len = self.focal_length if focal_length is None else focal_length
        ca = self.to_camera_space(world_a)
        cb = self.to_camera_space(world_b)
        clipped = clip_edge_near(ca, cb)
        if clipped is None:
            return None
        pa = self.project_relative(clipped[0], mode, centre=centre, focal_length=f_len)
        pb = self.project_relative(clipped[1], mode, centre=centre, focal_length=f_len)
        if pa is None or pb is None:
            return None
        return (pa, pb)

    def forward_vector(self) -> Point3D:
        """Return the unit forward vector in world space based on current yaw and pitch."""
        cp = cos(self.pitch)
        return (
            sin(self.yaw) * cp,
            -sin(self.pitch),
            cos(self.yaw) * cp,
        )

    def right_vector(self) -> Point3D:
        """Return the unit right strafe vector in world space."""
        return (cos(self.yaw), 0.0, -sin(self.yaw))
