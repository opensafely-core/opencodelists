"""
Parse WHO ICD-10 ClaML XML and extract 3-, 4- and modifier-derived 5-character codes
with their usage type (dagger/asterisk) and associated codes.

ClaML structure relevant here:

  <Class kind="chapter"   code="I">       ← chapter              (excluded)
  <Class kind="block"     code="A00-A09"> ← code range block      (excluded)
  <Class kind="category"  code="A00">     ← 3-char category       (included)
  <Class kind="category"  code="A00.0">   ← 4-char subcategory    (included)

Modifier system
---------------
Modifier definitions sit in two element types at the root level - but the content is duplicated
so we can parse all we need from the ModifierClass elements alone:

  <Modifier code="S04E10_4">          ← named modifier set; _4/_5 suffix = digit tier
    <SubClass code=".0"/>             ← ordered digit options
    ...
  </Modifier>

  <ModifierClass code=".0" modifier="S04E10_4">   ← digit with its description
    <Rubric kind="preferred"><Label>With coma</Label></Rubric>
  </ModifierClass>

A <Class> element may reference a modifier set:

  <Class kind="category" code="E10">
    <ModifiedBy code="S04E10_4"/>
    ...
  </Class>

Four expansion patterns (determined by tier suffix + whether the class has
4-char children):

  A. _4, 3 char with no 4-char children  (e.g. E10 + S04E10_4):
       digit codes include dot: ".0", ".1", ...
       generated code: base + digit → "E10.0"  (new 4-char code)
       description:    modifier digit label  ("With coma")

  B. _4, 3 char with 4-char children (e.g. I70 + I70M10_4):
       digit codes are bare: "0", "1"
       generated code: each 4-char child + digit → "I70.00"  (5-char)
       description:    child desc + " (" + modifier label + ")"

  C. _5, 3 char with no 4-char children  (e.g. M45 + S13M40_5):
       digit codes are bare: "0", "1", ...
       generated code: base + ".X" + digit → "M45.X0"  (5-char with X placeholder)
       description:    base desc + " (" + modifier label + ")"

  D. _5, 3 char with 4-char children (e.g. M00 + S13M00_5):
       digit codes are bare: "0", "1", ...
       generated code: each 4-char child + digit → "M00.00"  (5-char)
       description:    child desc + " (" + modifier label + ")"

  E. _5, 4 char code (e.g. T14.2)
       digit codes are bare: "0", "1", ...
       generated code: base + digit → "T14.20"
      description:    base desc + " (" + modifier label + ")"


Implicit ModifiedBy
-------------------
Some Class elements have a <Rubric kind="modifierlink"> referencing a modifier
set but no <ModifiedBy> element. These appear to be authoring gaps in the WHO
source. The parser detects them, asserts that only the known code(s) are
affected (currently only M13), and expands them as if <ModifiedBy> were
present.


Place of occurrence (W00–Y34)
-----------------------------
Per WHO ICD-10 coding guidance, a 4th character identifying place of occurrence
must be assigned to all codes in categories W00–Y34.  The place digits come from
modifier S20W00_4 (0=Home … 9=Unspecified) and are bare ("0"–"9"), so the dot is
inserted by the parser: base + "." + digit → e.g. W00 → W00.0.

Exceptions (own 4-char subcategories, no place expansion):
  Y06  Neglect and abandonment
  Y07  Other maltreatment

Deferred subcategory parents (W26, X34, X59):
  WHO introduced bespoke 4th-char subcategories for these three codes but UK
  practice has deferred that re-designation.  Their ClaML-defined 4-char
  children are therefore excluded from the parsed output; place codes are
  generated instead.

The activity modifier S20V01T_5 is intentionally ignored.

Facts from https://classbrowser.nhs.uk/ref_books/ICD-10_2026_5th_Ed_NCCS.pdf

1. 4th character modifiers for W00-Y34
  p217: A fourth character must be assigned with codes from categories W00-Y34
        to identify where the injury, poisoning or adverse effect took place.
        The fourth characters can be found in the ‘Place of occurrence code’
        section at the beginning of the chapter. The exceptions are codes in
        categories Y06.- Neglect and abandonment and Y07.- Other maltreatment.

  p219: ICD-10 provides an activity subclassification as an extra character for
        use with categories V01–Y34 to indicate the activity of the injured
        person at the time the event occurred. However, due to the general
        unavailability of this information, these activity subclassification
        codes shown at the beginning of this chapter must not be used."

  p220: The fourth character codes printed at categories
            W26.- Contact with other sharp object(s)
            X34.- Victim of earthquake and
            X59.- Exposure to unspecified factor
        in the ICD-10 Tabular List must not be used and must be crossed through
        in the ICD-10 5th Edition books. The content that must be crossed
        through can be found in the ICD-10 and OPCS-4 Classifications Content
        Changes document on Delen. The ‘Place of occurrence codes’ must be used
        for fourth character code assignment with categories W26, X34 and X59.


"""

import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path


# ---------------------------------------------------------------------------
# Code-pattern regexes
# ---------------------------------------------------------------------------
#  3-char: "A00" – "Z99"
THREE_CHAR_RE = re.compile(r"^[A-Z]\d{2}$")
#  4-char: "A00.0" – "Z99.9"
FOUR_CHAR_RE = re.compile(r"^[A-Z]\d{2}\.\d$")
#  5-char: "A00.00", "M45.X0", etc.  (4th position after dot: digit or X)
FIVE_CHAR_RE = re.compile(r"^[A-Z]\d{2}\.[\dX]\d$")


def is_three_char(code: str) -> bool:
    return bool(THREE_CHAR_RE.match(code))


def is_four_char(code: str) -> bool:
    return bool(FOUR_CHAR_RE.match(code))


def is_five_char(code: str) -> bool:
    return bool(FIVE_CHAR_RE.match(code))


# ---------------------------------------------------------------------------
# Place-of-occurrence constants
# ---------------------------------------------------------------------------
# Modifier that provides place digits 0–9 (Home, Residential institution, …)
PLACE_OF_OCCURRENCE_MODIFIER = "S20W00_4"
# All 3-char codes in this inclusive range must carry a place 4th character …
_PLACE_RANGE_START = "W00"
_PLACE_RANGE_END = "Y34"
# … except these two, which have their own specific 4-char subcategories.
_PLACE_EXCEPTIONS: frozenset[str] = frozenset({"Y06", "Y07"})

# Class elements that carry a <Rubric kind="modifierlink"> but no <ModifiedBy>.
# These are treated as implicit ModifiedBy references.  Any code found beyond
# this set causes a hard assertion failure.
_KNOWN_IMPLICIT_MODIFIEDBY: frozenset[str] = frozenset({"M13"})

# WHO introduced 4-char subcategories for 3 of these codes in 2016, and a
# further 4 codes in 2019. The NHS chooses to ignore those subcategories and
# uses the place of occurrence modifier for all 3-char codes in the range instead
# The below are all the codes in 2016 and 2019 that should be overwritte by
# place-of-occurrence generated codes.

_PLACE_MODIFIER_OVERRIDE_EXCEPTIONS: dict[str, frozenset[str]] = {
    "chapters.claml": frozenset(),  # no exceptions in the chapter-level XML
    "icd102016en": frozenset(
        {
            "W26.0",
            "W26.8",
            "W26.9",
            "X34.0",
            "X34.1",
            "X34.8",
            "X34.9",
            "X59.0",
            "X59.9",
        }
    ),
    "icd102019en": frozenset(
        {
            "W26.0",
            "W26.8",
            "W26.9",
            "X34.0",
            "X34.1",
            "X34.8",
            "X34.9",
            "X47.0",
            "X47.1",
            "X47.2",
            "X47.3",
            "X47.4",
            "X47.8",
            "X47.9",
            "X59.0",
            "X59.9",
            "X67.0",
            "X67.1",
            "X67.2",
            "X67.3",
            "X67.4",
            "X67.8",
            "X67.9",
            "X88.0",
            "X88.1",
            "X88.2",
            "X88.3",
            "X88.4",
            "X88.8",
            "X88.9",
            "Y17.0",
            "Y17.1",
            "Y17.2",
            "Y17.3",
            "Y17.4",
            "Y17.8",
            "Y17.9",
        }
    ),
}


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------
@dataclass
class ICD10Code:
    """A single ICD-10 code entry."""

    code: str
    parent: str | None
    description: str
    term_modifier: str | None = None
    modifier_position: int | None = None
    usage: str = None
    usage_pair_codes: tuple[str] = None

    def __repr__(self) -> str:
        return f"ICD10Code({self.code!r}, {self.description!r}{f' ({self.term_modifier!r})' if self.term_modifier else ''}{f', modifier_position={self.modifier_position!r}' if self.modifier_position else ''}, usage={self.usage!r}, usage_pair_codes={self.usage_pair_codes!r})"


@dataclass
class ModifierDigit:
    """One digit option within a modifier definition."""

    digit_code: str  # raw code from ModifierClass/@code, e.g. ".0", "0"
    description: str  # preferred label for this digit


# ---------------------------------------------------------------------------
# XML helpers
# ---------------------------------------------------------------------------
def _get_label_text(rubric_element: ET.Element) -> str:
    """Extract concatenated text from the first <Label> inside a <Rubric>.
    Excludes the text of <Reference> elements to avoid appending cross-reference
    (dagger/asterisk) codes to the description.

    Concatenates text from the label and all its non-Reference children. This
    can include text and nested elements e.g.:
    <Rubric id="D0020138" kind="preferred">
      <Label xml:lang="en" xml:space="default">
        <Term class="italics">In vitro</Term>
        fertilization
      </Label>
    </Rubric>

    or

    <Rubric id="D0003166" kind="preferred">
      <Label xml:lang="en" xml:space="default">
        Vitamin B
        <Term class="subscript">12</Term>
        deficiency anaemia, unspecified
      </Label>
    </Rubric>
    """
    label = rubric_element.find("Label")
    if label is None:
        return ""

    def _extract_text(el: ET.Element) -> str:
        res = [el.text or ""]
        for child in el:
            if child.tag == "Reference":
                # skip child's text and children, but keep its tail
                res.append(child.tail or "")
            else:
                res.append(_extract_text(child))
                res.append(child.tail or "")
        return "".join(res)

    return re.sub(r"\s+", " ", _extract_text(label)).strip()


def _parent(element: ET.Element) -> str | None:
    superclass = element.find("SuperClass")
    return superclass.get("code") if superclass is not None else None


def _preferred_description(element: ET.Element) -> str:
    """Assert element has exactly 1 rubric with kind="preferred" and return that."""
    rubrics = element.findall("Rubric")
    preferred = [r for r in rubrics if r.get("kind") == "preferred"]
    assert len(preferred) == 1, (
        f"Expected exactly one preferred Rubric in Class {element.get('code')!r}, "
        f"found {len(preferred)}"
    )
    return _get_label_text(preferred[0])


def _usage(element: ET.Element) -> tuple[str, list[str]]:
    if element.get("usage"):
        related_code_fragments = element.iter("Reference")
        related_codes = [el.text for el in related_code_fragments]
        return (element.get("usage"), tuple(related_codes))
    else:
        return (None, None)


def _items(root: list[ET.Element]) -> list[ET.Element]:
    """
    Return all the <Class> elements
    The three kinds of <Class> element in the claml are:
    - chapters (e.g. I, II, III, …)
    - blocks (e.g. A00-A09, A15-A19, …)
    - categories (e.g. A00, A01, …)
    """
    classes = root.findall("Class")
    items = []
    for c in classes:
        kind = c.get("kind")
        assert kind in {"chapter", "block", "category"}, "Unexpected class kind"
        items.append(c)

    return items


# ---------------------------------------------------------------------------
# Modifier parsing
# ---------------------------------------------------------------------------
def _parse_modifier_defs(
    modifierClasses: list[ET.Element],
) -> dict[str, list[ModifierDigit]]:
    """
    Build a map of modifier_id → ordered list of ModifierDigit from the
    <ModifierClass> elements.
    """

    modifier_defs: dict[str, list[ModifierDigit]] = {}
    for mc in modifierClasses:
        modifier_id = mc.get("modifier")
        digit_code = mc.get("code")
        desc = _preferred_description(mc)
        assert modifier_id and digit_code and desc, (
            "Malformed xml - all ModifierClass elements should have @modifier"
            ", @code and a Rubric with preferred label"
        )
        modifier_defs.setdefault(modifier_id, []).append(
            ModifierDigit(digit_code=digit_code, description=desc)
        )

    return modifier_defs


def _find_implicit_modifiedby(categories: list[ET.Element]) -> dict[str, str]:
    """
    Find Class elements that have a <Rubric kind="modifierlink"> but no
    <ModifiedBy> child, and return a mapping of code → modifier_id.

    The modifier id is read from the <Reference code="..."> inside the rubric
    label, e.g.:

      <Rubric kind="modifierlink">
        <Label><Reference code="S13M00_5">…</Reference></Label>
      </Rubric>
    """
    result: dict[str, str] = {}
    for cat in categories:
        if cat.find("ModifiedBy") is not None:
            continue
        for rubric in cat.findall("Rubric"):
            if rubric.get("kind") != "modifierlink":
                continue
            ref = rubric.find("Label/Reference")
            if ref is None:
                continue
            modifier_id = ref.get("code")
            if modifier_id:
                result[cat.get("code")] = modifier_id
    return result


def _combine(base_desc: str, modifier_desc: str) -> str:
    """Combine a base description with a modifier: 'Base (modifier)'."""
    assert base_desc and modifier_desc
    return f"{base_desc} ({modifier_desc})"


def _expand_modifiers(
    codes: dict[str, ICD10Code],
    categories: list[ET.Element],
    modifier_defs: dict[str, list[ModifierDigit]],
    implicit_modifiedby: dict[str, str] | None = None,
) -> dict[str, ICD10Code]:
    """
    Generate modifier-derived codes and return them as a new dict.

    Only processes 3-character base classes; modifier application to blocks
    or other non-category elements is intentionally skipped.
    Existing codes in *codes* are never overwritten.

    *implicit_modifiedby* supplies modifier ids for Class elements that carry a
    modifierlink rubric but no <ModifiedBy> element.
    """
    modifier_codes: dict[str, ICD10Code] = {}
    _implicit = implicit_modifiedby or {}

    for cat in categories:
        base_code = cat.get("code")

        mb = cat.find("ModifiedBy")
        if mb is None:
            modifier_id = _implicit.get(base_code)
            if modifier_id is None:
                continue
        else:
            modifier_id = mb.get("code")

        if modifier_id == PLACE_OF_OCCURRENCE_MODIFIER:
            continue

        digits = modifier_defs.get(modifier_id)

        tier = 5 if modifier_id.endswith("_5") else 4

        child_codes = [sub.get("code") for sub in cat.findall("SubClass")]

        # assert child codes, where they exist are always 4-char, for sanity check
        assert all(is_four_char(c) for c in child_codes), (
            "Expected all modifier child codes to be 4-character"
        )

        base_desc = codes[base_code].description

        if child_codes:
            # Pattern B: _4 modifier, with 4-char children → 5-char codes e.g. I70
            # Pattern D: _5 modifier, with 4-char children → 5-char codes e.g. M00
            for child_code in child_codes:
                child_desc = codes[child_code].description
                for d in digits:
                    new_code = child_code + d.digit_code  # "M00.0" + "0" = "M00.00"
                    modifier_codes[new_code] = ICD10Code(
                        code=new_code,
                        parent=base_code,
                        description=child_desc,
                        term_modifier=d.description,
                        modifier_position=tier,
                    )
        else:
            for d in digits:
                if tier == 5:
                    if is_four_char(base_code):
                        # Pattern E: _5 modifier, 4 char code → new 5-char codes
                        new_code = base_code + d.digit_code  # "T14.2" + "0" = "T14.20"
                    else:
                        # Pattern C: _5 modifier, no 4-char children
                        new_code = (
                            base_code + ".X" + d.digit_code
                        )  # "M45" + ".X" + "0" = "M45.X0"
                elif tier == 4:
                    # Pattern A: _4 modifier, no 4-char children → new 4-char codes
                    # Digit codes already include the dot: ".0", ".1", ...
                    new_code = base_code + d.digit_code  # "E10" + ".0" = "E10.0"

                modifier_codes[new_code] = ICD10Code(
                    code=new_code,
                    parent=base_code,
                    description=base_desc,
                    term_modifier=d.description,
                    modifier_position=tier,
                )

    return modifier_codes


def _expand_place_of_occurrence(
    codes: dict[str, ICD10Code],
    modifier_defs: dict[str, list[ModifierDigit]],
) -> dict[str, ICD10Code]:
    """
    Generate place-of-occurrence 4-char codes for all 3-char codes in the
    W00–Y34 range (except Y06 and Y07).
    """
    digits = modifier_defs.get(PLACE_OF_OCCURRENCE_MODIFIER)
    place_modified_codes: dict[str, ICD10Code] = {}
    for base_code in list(codes):
        if not is_three_char(base_code):
            continue
        if not (_PLACE_RANGE_START <= base_code <= _PLACE_RANGE_END):
            continue
        if base_code in _PLACE_EXCEPTIONS:
            continue

        base_desc = codes[base_code].description
        for d in digits:
            new_code = (
                base_code + "." + d.digit_code
            )  # e.g. "W00" + "." + "0" = "W00.0"
            place_modified_codes[new_code] = ICD10Code(
                code=new_code,
                parent=base_code,
                description=base_desc,
                term_modifier=d.description,
                modifier_position=4,
            )
    return place_modified_codes


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------
def parse_claml(xml_path: str | Path) -> dict[str, ICD10Code]:
    """
    Parse a ClaML XML file and return a mapping of code → ICD10Code.
    """
    root = ET.parse(str(xml_path)).getroot()
    icd_items = _items(root)
    categories = [item for item in icd_items if item.get("kind") == "category"]

    codes: dict[str, ICD10Code] = {}

    for item in icd_items:
        code = item.get("code")
        usage, usage_pair_codes = _usage(item)
        codes[code] = ICD10Code(
            code=code,
            parent=_parent(item),
            description=_preferred_description(item),
            usage=usage,
            usage_pair_codes=usage_pair_codes,
        )

    # Add the modifier-derived codes to the main code dict
    # The modifier definitions are in the ModifierClass elements
    modifier_defs = _parse_modifier_defs(root.findall("ModifierClass"))

    # Detect Class elements with a modifierlink rubric but no ModifiedBy and
    # assert that only the known set of codes is affected.
    implicit = _find_implicit_modifiedby(categories)
    unexpected = set(implicit) - _KNOWN_IMPLICIT_MODIFIEDBY
    assert not unexpected, (
        f"Unexpected Class elements with modifierlink but no ModifiedBy: "
        f"{sorted(unexpected)}"
    )

    modifier_codes = _expand_modifiers(codes, categories, modifier_defs, implicit)
    # assert overlap of generated modifier codes with existing codes is empty, for sanity check
    overlap = set(modifier_codes) & set(codes)
    assert not overlap, "Generated modifier codes overlap with existing codes"
    codes.update(modifier_codes)

    # Place of occurrence modifiers are a bit different and so done separately
    place_modified_codes = _expand_place_of_occurrence(codes, modifier_defs)
    # assert overlap of place-generated codes with existing codes only contains codes
    # with deferred subcategories (W26, X34, X59), for sanity check
    overlap = set(place_modified_codes) & set(codes)
    expected_overlap = _PLACE_MODIFIER_OVERRIDE_EXCEPTIONS.get(xml_path.stem, set())
    assert overlap == expected_overlap, (
        "Place-of-occurrence generated codes overlap with existing codes"
    )
    codes.update(place_modified_codes)

    return codes


# Not called if run via main, but useful for debugging the parser in isolation.
# TODO REMOVE
if __name__ == "__main__":
    parse_claml(Path(".cache") / "icd102016en.xml")
    parse_claml(Path(".cache") / "icd102019en.xml")
