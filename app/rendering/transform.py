@dataclass
class Transform:
    logical_width: float
    logical_height: float
    physical_width: float
    physical_height: float

    @property
    def scale(self) -> float:

        return min(
            self.physical_width
            / self.logical_width,

            self.physical_height
            / self.logical_height,
        )

    @property
    def offset_x(self) -> float:

        return (
            self.physical_width
            - self.logical_width * self.scale
        ) / 2

    @property
    def offset_y(self) -> float:

        return (
            self.physical_height
            - self.logical_height * self.scale
        ) / 2

    def position(
        self,
        x: float,
        y: float,
    ) -> tuple[float, float]:

        return (
            self.offset_x
            + x * self.scale,

            self.offset_y
            + y * self.scale,
        )

    def size(
        self,
        width: float,
        height: float,
    ) -> tuple[float, float]:

        return (
            width * self.scale,
            height * self.scale,
        )