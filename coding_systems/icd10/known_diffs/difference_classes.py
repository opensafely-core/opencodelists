from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CodeDifference:
    include_in_release: bool


@dataclass(frozen=True, slots=True)
class TermDifference:
    claml: str
    scraped: str
    use: str

    def __post_init__(self) -> None:
        if self.use not in ("claml", "scraped"):
            raise ValueError(f"use must be 'claml' or 'scraped', got {self.use!r}")


@dataclass(frozen=True, slots=True)
class ReleaseTermDifference:
    combined_2016: str
    who_2019: str
    clinically_equivalent: bool
