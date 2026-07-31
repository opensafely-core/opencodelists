from dataclasses import dataclass, field


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
class KnownDifferences:
    claml_only: dict[str, CodeDifference]
    scraped_only: dict[str, CodeDifference]
    term_differences: dict[str, TermDifference]


@dataclass(frozen=True, slots=True)
class ReleaseTermDifference:
    combined_2016: str
    who_2019: str
    clinically_equivalent: bool


@dataclass
class RubricDifference:
    """
    Represents a change to the rubrics of a code between releases. This can
    include additions, removals, and replacements of rubric text. The `who_2016`
    field represents the original rubrics from the 2016 WHO release, while the
    `remove`, `add`, and `replace` fields represent the changes to be applied.
    """

    who_2016: dict[str, list[str]] = field(default_factory=dict)
    remove: dict[str, list[str]] = field(default_factory=dict)
    add: dict[str, list[str]] = field(default_factory=dict)
    replace: dict[str, dict[str, str]] = field(default_factory=dict)
    comment: str = ""

    @property
    def resolved_rubrics(self) -> dict[str, list[str]]:
        """
        Resolve the rubric changes by applying removals, additions, and replacements
        to the original WHO rubrics. Returns a dictionary of rubric types to their
        final list of values after applying the changes.
        """
        rubrics = {
            # Using list() to create a shallow copy of the list to avoid mutating
            # the original WHO rubrics
            rubric_type: list(values)
            for rubric_type, values in self.who_2016.items()
        }

        for rubric_type, replacements in self.replace.items():
            for text_to_find, text_to_replace in replacements.items():
                rubrics[rubric_type] = [
                    v.replace(text_to_find, text_to_replace)
                    for v in rubrics[rubric_type]
                ]

        for rubric_type, values_to_remove in self.remove.items():
            values = rubrics[rubric_type]
            for value in values_to_remove:
                values.remove(value)
            if not values:
                del rubrics[rubric_type]

        for rubric_type, values_to_add in self.add.items():
            rubrics.setdefault(rubric_type, []).extend(values_to_add)

        return rubrics
