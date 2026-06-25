import importlib
import json
import xml
from copy import deepcopy
from pathlib import Path

import coding_systems.icd10.scraped_to_claml as scraped_to_claml


SCRAPED_FIXTURE = Path(__file__).parent.parent / "fixtures" / "scraped.json"


def test_convert_chapters_to_claml(tmp_path):
    chapters = json.load(SCRAPED_FIXTURE.open())
    claml_path = tmp_path / "claml.xml"

    scraped_to_claml.convert_chapters_to_claml(chapters, claml_path)

    claml = xml.etree.ElementTree.parse(claml_path).getroot()

    assert len(claml.findall(".//Class[@kind='chapter']")) == 2
    assert len(claml.findall(".//Class[@kind='block']")) == 20
    assert len(claml.findall(".//Class[@kind='category']")) == 717


def test_convert_chapters_to_claml_produces_same_result(tmp_path):
    def inverse_sort_values(dict_obj):
        for k, v in dict_obj.items():
            if isinstance(v, list):
                dict_obj[k] = sorted(v, reverse=True)
            if isinstance(v, dict):
                dict_obj[k] = inverse_sort_values(v)
        return dict_obj

    chapters = json.load(SCRAPED_FIXTURE.open())
    claml_path = tmp_path / "claml.xml"
    claml2_path = tmp_path / "claml2.xml"

    importlib.reload(scraped_to_claml)
    scraped_to_claml.convert_chapters_to_claml(chapters, claml_path)

    shuffled_chapters = deepcopy(chapters)
    shuffled_chapters = inverse_sort_values(shuffled_chapters)
    assert shuffled_chapters != chapters
    importlib.reload(scraped_to_claml)
    scraped_to_claml.convert_chapters_to_claml(shuffled_chapters, claml2_path)

    assert claml_path.read_text() == claml2_path.read_text()
