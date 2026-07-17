import re
import xml.etree.ElementTree as etree
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum, EnumMeta, auto
from itertools import count
from pathlib import Path


JSON_PATH = Path("icdscrape/chapters.json")
CLAML_PATH = Path("icdscrape/chapters.xml")

CLAML_HEADER = """
<!DOCTYPE ClaML SYSTEM "ClaML.dtd">
<ClaML version="2.0.0">
	<Meta name="TopLevelSort" value="I II III IV V VI VII VIII IX X XI XII XIII XIV XV XVI XVII XVIII XIX XX XXI XXII"/>
	<Meta name="lang" value="en"/>
	<Identifier authority="NHS" uid="icd10_2016_scraped"/>
	<Title date="2016-04-01" name="ICD-10-EN-2016" version="2016">International Statistical Classification of Diseases and Related Health Problems 10th Revision</Title>
</ClaML>
"""

D_ID_COUNT = count(1)
TBAL_ID_COUNT = count()
SECTIONAL_MODIFIER_ID_COUNT = count(1)

REFERENCE_PATTERN = re.compile(r"\( ?[A-Z][0-9]{2,}[^\)]* \)")

classes_to_write = []


def d_id():
    return f"D{next(D_ID_COUNT):07d}"


def tbal_id():
    return f"id-to-be-added-later-1210506823253-{next(TBAL_ID_COUNT)}"


def _sorted_items(_dict):
    return sorted(_dict.items(), key=lambda item: item[0])


class KindEnumMeta(EnumMeta):
    def __getitem__(self, name):
        return super().__getitem__(name.upper().replace("-", "_"))


class KindEnum(Enum, metaclass=KindEnumMeta):
    def __str__(self):
        return self.name.lower()

    def to_sub_element(self):
        subelem = etree.Element(self.__class__.__name__)
        subelem.attrib["name"] = str(self)
        return subelem

    @classmethod
    def to_element(cls):
        elem = etree.Element(f"{cls.__name__}s")
        for member in cls:
            elem.append(member.to_sub_element())
        return elem


class ClassKind(KindEnum):
    CATEGORY = auto()
    BLOCK = auto()
    CHAPTER = auto()


class UsageKindMeta(KindEnumMeta):
    def __getitem__(self, name):
        return self.__call__(name.replace("†", "+"))


class UsageKind(KindEnum, metaclass=UsageKindMeta):
    ASTER = "*"
    DAGGER = "+"

    def to_sub_element(self):
        sub_element = super().to_sub_element()
        sub_element.attrib["mark"] = self.value
        return sub_element


class RubricKind(KindEnum):
    FOOTNOTE = auto()
    TEXT = auto()
    CODING_HINT = auto()
    DEFINITION = auto()
    INTRODUCTION = auto()
    MODIFIERLINK = auto()
    NOTE = auto()
    EXCLUSION = auto()
    INCLUSION = auto()
    PREFERREDLONG = auto()
    PREFERRED = auto()
    # UK edition specific:
    SMALL = auto()
    SMALL2 = auto()
    SMALL3 = auto()
    SMALL2PLAIN = auto()

    def __str__(self):
        return super().__str__().replace("_", "-")

    def to_sub_element(self):
        sub_element = super().to_sub_element()
        sub_element.attrib["inherited"] = "false"
        return sub_element


class Element:
    def to_element(self):
        elem = etree.Element(self.__class__.__name__)
        for attr, value in self.__dict__.items():
            if isinstance(value, str) or isinstance(value, KindEnum):
                elem.attrib[attr] = str(value)
            if isinstance(value, list):
                for v in value:
                    elem.append(v.to_element())
            if isinstance(value, Element):
                elem.append(value.to_element())

        return elem


@dataclass
class SubClass(Element):
    code: str


@dataclass
class SuperClass(Element):
    code: str


@dataclass
class Rubric(Element):
    kind: RubricKind
    label: str
    id: str | None = None

    def __post_init__(self):
        self.id = (
            d_id()
            if self.kind in [RubricKind.PREFERRED or RubricKind.INCLUSION]
            else tbal_id()
        )

    def _get_label_with_references(self):
        def add_references_to_element(elem):
            if references := REFERENCE_PATTERN.findall(elem.text):
                remaining_text = self.label.strip()
                for i, reference in enumerate(references):
                    if "," in reference:
                        references.pop(i)
                        references.extend(reference.split(","))

                for reference in references:
                    ref_elem = etree.Element("Reference")
                    ref_elem.attrib["class"] = "in brackets"
                    code = reference.strip("() *†")
                    ref_elem.attrib["code"] = code.split(" ")[0].split("-")[0]
                    if "*" in reference or "†" in reference:
                        ref_elem.attrib["usage"] = (
                            "aster" if "*" in reference else "dagger"
                        )
                    ref_elem.text = code
                    elem.append(ref_elem)
                    remaining_text = remaining_text.replace(reference, "").strip(" ,")
                if "*" in remaining_text or "†" in remaining_text:
                    elem.attrib["usage"] = (
                        "aster" if "*" in remaining_text else "dagger"
                    )
                    remaining_text = (
                        remaining_text.replace("*", "").replace("†", "").strip(" ,")
                    )
                elem.text = remaining_text

        label_elem = etree.Element("Label")
        label_elem.attrib[
            etree.QName("http://www.w3.org/XML/1998/namespace", "lang")
        ] = "en"  # type: ignore
        label_elem.attrib[
            etree.QName("http://www.w3.org/XML/1998/namespace", "space")
        ] = "default"  # type: ignore
        if ": " in self.label:
            frag1, frag2 = self.label.split(": ", 1)
            frag1_elem = etree.Element("Fragment")
            frag1_elem.attrib["type"] = "list"
            frag1_elem.text = frag1 + ":"

            frag2_elem = etree.Element("Fragment")
            frag2_elem.attrib["type"] = "list"
            frag2_elem.text = frag2
            for frag_elem in [frag1_elem, frag2_elem]:
                add_references_to_element(frag_elem)
            label_elem.append(frag1_elem)
            label_elem.append(frag2_elem)
            return label_elem
        else:
            label_elem.text = self.label
            add_references_to_element(label_elem)
            return label_elem

    def to_element(self):
        elem = super().to_element()
        del elem.attrib["label"]
        elem.append(self._get_label_with_references())
        return elem

    @classmethod
    def preferred_label_from_values(cls, values):
        label_suffix = ""
        if values.get("dagger_asterisk") and (
            related_codes := values.get("related_codes")
        ):
            # re-introduce bracketed reference string to label if there are
            # related codes which are not related via rubrics
            rubrics = values.get("rubric", {})
            has_dagger_asterisk_in_rubric = False
            for rubric in rubrics.values():
                for r in rubric:
                    if "*" in r or "†" in r:
                        has_dagger_asterisk_in_rubric = True
                        break
            if not has_dagger_asterisk_in_rubric:
                label_suffix = f" ( {', '.join(sorted(related_codes))} )"
        return Rubric(
            kind=RubricKind.PREFERRED,
            label=values["title"] + label_suffix,
        )


@dataclass
class ModifiedBy(Element):
    code: str


@dataclass
class Class(Element):
    code: str
    kind: ClassKind | None
    superclass: SuperClass | None = None
    subclasses: list[SubClass] = field(default_factory=list)
    rubrics: list[Rubric] = field(default_factory=list)
    modifiedby: ModifiedBy | None = None
    usage: UsageKind | None = None


@dataclass
class Modifier(Element):
    code: str
    subclasses: list[SubClass] = field(default_factory=list)
    rubrics: list[Rubric] = field(default_factory=list)


@dataclass
class ModifierClass(Class):
    modifier: str | None = None


def append_element_rubrics(elem, values):
    if rubrics := values.get("rubric"):
        for rubric_type, rubrics in _sorted_items(rubrics):
            for rubric in sorted(rubrics):
                elem.rubrics.append(Rubric(kind=RubricKind[rubric_type], label=rubric))  # type: ignore


def get_base_class_element(code, values, kind, super_code=None):
    elem = Class(code=code, kind=kind)
    if super_code:
        elem.superclass = SuperClass(super_code)
    elem.rubrics.append(Rubric.preferred_label_from_values(values))
    append_element_rubrics(elem, values)
    return elem


def generate_chapter_element(chapter_code, chapter_values):
    chapter_elem = get_base_class_element(
        chapter_code, chapter_values, ClassKind.CHAPTER
    )
    for block in _sorted_items(chapter_values["blocks"]):
        chapter_elem.subclasses.append(
            SubClass(code=generate_block_element(*block, super_code=chapter_code))
        )

    classes_to_write.append(chapter_elem)
    extract_modifiers(chapter_elem, chapter_values)


def generate_block_element(block_code, block_values, super_code):
    block_elem = get_base_class_element(
        block_code, block_values, ClassKind.BLOCK, super_code
    )
    if sub_blocks := block_values.get("blocks"):
        for sub_block in _sorted_items(sub_blocks):
            block_elem.subclasses.append(
                SubClass(generate_block_element(*sub_block, super_code=block_code))
            )
    elif categories := block_values.get("categories"):
        for category in _sorted_items(categories):
            block_elem.subclasses.append(
                SubClass(generate_category_element(*category, super_code=block_code))
            )
    classes_to_write.append(block_elem)
    extract_modifiers(block_elem, block_values)
    return block_code


def generate_category_element(category_code, category_values, super_code):
    category_element = get_base_class_element(
        category_code, category_values, ClassKind.CATEGORY, super_code
    )
    if dagger_asterisk := category_values.get("dagger_asterisk"):
        category_element.usage = UsageKind[dagger_asterisk]  # type: ignore
    if categories := category_values.get("categories"):
        for category in _sorted_items(categories):
            category_element.subclasses.append(
                SubClass(generate_category_element(*category, super_code=category_code))
            )
    classes_to_write.append(category_element)
    extract_modifiers(category_element, category_values)
    return category_code


modifiers_to_apply = defaultdict(list[Modifier])


def extract_modifiers(_class: Class, values: dict):
    if modifiers := values.get("modifiers"):
        modifier_range = modifiers.get("modifier_range")
        if not modifier_range:
            if _class.subclasses and _class.kind != ClassKind.CATEGORY:
                sorted_subclasses = sorted([sc.code for sc in _class.subclasses])
                range_start = sorted_subclasses[0].split("-")[0]
                range_end = sorted_subclasses[-1].split("-")[-1]
                modifier_range = f"{range_start}-{range_end}"
            else:
                modifier_range = f"{_class.code}-{_class.code}"
        assert len([char for char in modifier_range if char == "-"]) <= 1

        modifier_code = f"{modifier_range.split('-')[0].replace('.', '')}_"
        if _class.kind != ClassKind.CATEGORY:
            modifier_code = f"S{next(SECTIONAL_MODIFIER_ID_COUNT):02d}_{modifier_code}"
        modifiers = modifiers["modifiers"]
        modifier_code += "4" if next(iter(modifiers)).startswith(".") else "5"

        modifier_elem = Modifier(modifier_code)
        for code_modifier, label_modifier in _sorted_items(modifiers):
            modifier_elem.subclasses.append(SubClass(code_modifier))
            modifier_class_elem = ModifierClass(
                code=code_modifier,
                modifier=modifier_code,
                superclass=SuperClass(code=modifier_code),
                rubrics=[Rubric(RubricKind.PREFERRED, label=label_modifier)],
                kind=None,
            )
            classes_to_write.append(modifier_class_elem)
        modifiers_to_apply[modifier_range].append(modifier_elem)


def apply_modifiers():
    categories = sorted(
        [c for c in classes_to_write if c.kind == ClassKind.CATEGORY],
        key=lambda c: c.code,
    )
    for modifier_range, modifiers in sorted(
        modifiers_to_apply.items(), key=lambda x: x[0]
    ):
        # we should only ever have one modifier for a given modifier range
        assert len(modifiers) == 1
        modifier = modifiers[0]
        classes_to_write.append(modifier)

        range_start, *_, range_finish = modifier_range.split("-")
        single_category_modifier = range_start == range_finish

        for category in categories:
            if range_start <= category.code <= range_finish:
                parent_categories = [
                    c
                    for c in categories
                    if c.kind == ClassKind.CATEGORY
                    and c.code == category.superclass.code
                ]
                # categories should only ever have one parent, which may or may not itself be a category
                assert len(parent_categories) <= 1
                parent_modifier = (
                    parent_categories[0].modifiedby.code
                    if parent_categories and parent_categories[0].modifiedby
                    else None
                )
                # Don't apply the modifier if the parent category is already modified by the same modifier
                if parent_modifier and parent_modifier == modifier.code:
                    continue
                # Don't apply inherited modifier (e.g. defined at Chapter or Block level)
                # if the category doesn't have a modifierlink rubric
                if not (
                    single_category_modifier and range_start == category.code
                ) and not any(
                    [r for r in category.rubrics if r.kind == RubricKind.MODIFIERLINK]
                ):
                    continue
                category.modifiedby = ModifiedBy(code=modifier.code)


def append_subclasses():
    for _class in classes_to_write:
        for child in [
            c
            for c in classes_to_write
            if c.superclass and c.superclass.code == _class.code
        ]:
            _class.subclasses.append(SubClass(code=child.code))


def convert_chapters_to_claml(chapters, claml_path):
    claml = etree.fromstring(CLAML_HEADER)
    claml.append(ClassKind.to_element())
    claml.append(UsageKind.to_element())
    claml.append(RubricKind.to_element())

    for chapter in chapters.items():
        generate_chapter_element(*chapter)

    apply_modifiers()

    for _class in classes_to_write:
        claml.append(_class.to_element())
    xml = etree.ElementTree(claml)
    etree.indent(xml, space="\t", level=0)
    xml.write(claml_path, xml_declaration=True, encoding="UTF-8")
