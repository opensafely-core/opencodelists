import json
import os
import re
import traceback
from collections import defaultdict
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib import parse

import requests as rq
from bs4 import BeautifulSoup, element


BASE_URL = "https://classbrowser.nhs.uk/"
errors = {}


def get_element_text_only(elem):
    return "".join(
        (" " + child.text + " ").replace("  ", " ")
        if not isinstance(child, element.NavigableString)
        else child.strip()
        for child in elem.contents
        if not isinstance(child, element.Comment)
        and (isinstance(child, element.NavigableString) or child.name == "a")
    )


def download_stream(url, path):
    resp = rq.get(url, stream=True)
    with path.open("wb") as f:
        for chunk in resp.iter_content(chunk_size=10240):
            f.write(chunk)


def fetch_menu_json():
    url = BASE_URL + "ICD-10-5TH-Edition/" + "ICD-10-5TH-Edition.json"
    r = rq.get(url, stream=True)
    return json.load(r.raw)


def get_block_urls(menu_json_path):
    block_url_pattern = r"ICD-10-5TH-Edition/vol1/block-[a-z\-0-9]+\.htm"
    return sorted(
        {
            BASE_URL + match
            for match in re.findall(block_url_pattern, menu_json_path.read_text())
        }
    )


def get_menu_chapters(menu, html_dir):
    def fetch_html(url, force_download=False):
        htmls_dir = html_dir / "html_cache"
        htmls_dir.mkdir(parents=True, exist_ok=True)
        file_path = htmls_dir / os.path.split(parse.urlparse(url).path)[-1]
        if force_download or not file_path.exists():
            download_stream(url, file_path)
        return file_path

    def split_text(text):
        return text.split(": ")

    def get_all_child_block_urls(child_block):
        if "id" in child_block:
            yield child_block["id"].split("#")[0]
        if child_block.get("children"):
            for grandchild in child_block.get("children"):
                yield from get_all_child_block_urls(grandchild)

    def get_blocks(chapter):
        if "children" in chapter:
            code, title = split_text(chapter["text"])
            url = chapter["id"]
            parsed_block = {}
            block_html_path = block_htmls.get(url.split("#")[0])
            if block_html_path:
                try:
                    parsed_block = parse_block_html(block_html_path, code)
                except Exception:
                    errors[code] = traceback.format_exc()
            return (
                code,
                {
                    "title": title,
                    "url": url,
                    "blocks": {
                        block[0]: block[1]
                        for child in chapter["children"]
                        if (block := get_blocks(child))
                    },
                    **parsed_block,
                },
            )

    vol_1 = None
    for chapter in menu["children"]:
        if chapter["text"] == "Volume 1 – Tabular list":
            vol_1 = chapter
            break
    if not vol_1:
        raise ValueError("Could not find Volume I menu section")
    tabular_list = None
    for chapter in vol_1["children"]:
        if (
            chapter["text"]
            == "Tabular list of inclusions and four-character subcategories"
        ):
            tabular_list = chapter
            break
    if not tabular_list:
        raise ValueError("Could not find 'tabular list of inclusions...' menu section")
    for chapter in tabular_list["children"]:
        number, title = split_text(chapter["text"])
        chapter_html = fetch_html(BASE_URL + chapter["id"])
        parsed_chapter = {}
        try:
            parsed_chapter = parse_chapter_html(chapter_html)
        except Exception:
            errors[str(chapter_html)] = traceback.format_exc()
        # multiple blocks can appear at the same URL
        # build a distinct list for convenience
        # and to avoid repeated downloads
        block_urls = set()
        for block_url in [
            set(get_all_child_block_urls(child)) for child in chapter["children"]
        ]:
            block_urls |= block_url
        block_urls = sorted(list(block_urls))
        block_htmls = {url: fetch_html(BASE_URL + url) for url in block_urls}
        blocks = get_blocks(chapter)[1]["blocks"]

        yield (
            number,
            {
                "title": title,
                "url": chapter["id"],
                "blocks": blocks,
                **parsed_chapter,
            },
        )


def label_text(elem):
    label = " ".join(
        "".join(
            [
                c.text
                for c in elem.children
                if isinstance(c, element.NavigableString)
                or (isinstance(c, element.Tag) and c.name == "sub")
                or (
                    isinstance(c, element.Tag)
                    and (c.name == "span" and "italics" in c.attrs["class"])
                )
            ]
        ).split()
    )
    if " )" in label or "()" in label:
        label = label.strip("() ,")
    if "(" in label and ")" not in label:
        label = label + ")"
    return label


def extract_dagger_asterisk_relation(elem):
    relations = []
    if isinstance(elem, element.Tag):
        for child in elem.children:
            relations += extract_dagger_asterisk_relation(child)
        if elem.name == "a":
            href = elem.attrs.get("href")
            if href:
                if isinstance(href, element.AttributeValueList):
                    href = href[0]
                if href.startswith("block-"):
                    relations.append(elem.text)
    return relations


def get_rubric(elem, return_element=False):
    def parse_rubric_ul(rubric_ul, parent_text):
        for rubric_li in rubric_ul.find_all("li", recursive=False):
            li_text = get_element_text_only(rubric_li).strip("—")
            if rubric_li_ul := rubric_li.find("ul", recursive=False):
                yield from parse_rubric_ul(rubric_li_ul, li_text)
            yield (parent_text + " " + li_text)

    rubric = defaultdict(list)
    for rubric_dl in elem.find_all(
        "dl", class_=lambda x: x and x.startswith("Rubric-")
    ):
        rubric_type = rubric_dl["class"][0].replace("Rubric-", "")
        if return_element:
            rubric[rubric_type] = rubric_dl
        else:
            rubric_dds = rubric_dl.find_all("dd")
            for rubric_dd in rubric_dds:
                if (rubric_ul := rubric_dd.find("ul")) and rubric_ul.find_all("li"):
                    parent_text = get_element_text_only(rubric_dd)
                    rubric[rubric_type].extend(parse_rubric_ul(rubric_ul, parent_text))

                else:
                    rubric[rubric_type].append(
                        rubric_dd.get_text(" ", strip=True).strip()
                    )
    return rubric


def get_modifiers(elem, force_prefix=""):
    modifier_table = elem.find("table", class_="ModifierTable")
    # bug with reconstituted divs
    while not modifier_table:
        for child in elem.children:
            if isinstance(child, element.Tag):
                modifier_table = child.find("table", class_="ModifierTable")
        if not modifier_table:
            return

    modifiers = {}
    for tr in modifier_table.tbody.find_all("tr"):
        code = tr.find("td", class_="modifierCode")
        title = tr.find("div", class_="modifierTitle")
        if code and title:
            modifiers[force_prefix + code.text.replace("\u2020", "")] = (
                title.text.strip()
            )
    modifier_range = ""
    # try to find modifier applicability ranges
    if modifier_block := elem.find("dl", class_="ModifierBlock"):
        for modifier_p in modifier_block.dd.find_all("p"):
            modifier_text = modifier_p.text
            for modifier_range_prelude in [
                "the following fourth-character subdivisions",
                "the following categories are provided to to be used",  # yes, really "to to"
            ]:
                if modifier_text.lower().strip().startswith(modifier_range_prelude):
                    if modifier_range := re.findall(
                        r"[A-Z]\d\d-[A-Z]\d\d", modifier_text
                    ):
                        modifier_range = modifier_range[0]
                        break

    return trim_dict({"modifiers": modifiers, "modifier_range": modifier_range})


def trim_dict(_dict):
    return {k: v for k, v in _dict.items() if v}


def parse_block_html(html_path, block_code):
    def is_block_div(div):
        # depending on how div is constructed, class may be str or list[str]
        _class = div.attrs.get("class")
        return _class == "Block" or (_class and "Block" in _class)

    def construct_block_div(block_element, contents=None):
        block_div = element.Tag(name="div", attrs={"class": "Block"})
        block_div.append(
            element.Tag(
                name="span",
                attrs={
                    "class": "valid_tree_node",
                    "id": block_element.attrs.get("id"),
                },
            )
        )
        if contents:
            block_div.contents.extend(contents)
        else:
            for sibling in block_element.find_next_siblings():
                if (
                    sibling.name == "span"
                    and sibling.attrs.get("class") == ["valid_tree_node"]
                ) or (sibling.name == "div" and is_block_div(sibling)):
                    break
                block_div.append(sibling)
        return block_div

    body = get_html_body(html_path)

    # chapter xx and xxi have flat structure within main "classicont" div,
    # replace with standardised hierarchical
    if not body.find_all("div", class_="Block"):
        classicont_div = body.find("div", id="classicont")

        # v01-v09 uses h3 whose "name" and "id" are equal instead of a span to indicate a block,
        # and a classless following div because why not?
        for h3 in classicont_div.find_all("h3", recursive=False):
            if (h3name := h3.attrs.get("name")) and (h3id := h3.attrs.get("id")):
                if not h3name == h3id:
                    continue
                h3_block_div = h3.find_next_sibling("div")
                new_block_div = construct_block_div(h3, h3_block_div.children)
                h3_block_div.replace_with(new_block_div)

        # now do the other block spans which have no following divs at all
        for block_span in classicont_div.find_all(
            "span", class_="valid_tree_node", recursive=False
        ):
            block_div = construct_block_div(block_span)
            block_span.replace_with(block_div)

    block_span = body.find("span", id=block_code)
    if not block_span:
        raise ValueError("Unable to find block span")

    block_div = block_span.parent
    # chapter XX has block spans wrapped in an h3 so we need to keep going up levels until we hit our block div
    while block_div.name != "div":
        block_div = block_div.parent
        if is_block_div(block_div):
            break

    if not is_block_div(block_div):
        raise ValueError("Unable to find block div")

    rubric = get_rubric(block_div)
    modifiers = get_modifiers(block_div)

    # only return the categories that immediately follow
    categories = {}
    category_modifier_fixes = {}
    for sibling_div in block_div.find_next_siblings("div"):
        if is_block_div(sibling_div):
            break
        if sibling_div.attrs.get("class") not in [["Category1"], ["Category2"]]:
            continue
        code_elem = sibling_div.find("a", class_="code")
        code = str(code_elem.attrs["id"])
        dagger_asterisk = code_elem.text.replace(code, "")
        label_elem = sibling_div.find("span", class_="label")
        label = label_text(label_elem)
        related_codes = extract_dagger_asterisk_relation(label_elem)
        category_rubric = get_rubric(sibling_div)
        category_inclusion_rubric_elem = get_rubric(
            sibling_div, return_element=True
        ).get("inclusion")
        if category_inclusion_rubric_elem:
            related_codes += extract_dagger_asterisk_relation(
                category_inclusion_rubric_elem
            )
        category_modifiers = get_modifiers(sibling_div) or category_modifier_fixes.get(
            code
        )

        # hack alert! The HTML in this section is malformed, this is horrible
        if code == "O02.9":
            category_modifier_fixes = {
                _code: category_modifiers for _code in ["O03", "O04", "O05", "O06"]
            }
            category_modifiers = None
        category = trim_dict(
            {
                "title": label,
                "rubric": category_rubric,
                "modifiers": category_modifiers,
                "dagger_asterisk": dagger_asterisk,
                "related_codes": list(set(related_codes)),
            }
        )

        if sibling_div.attrs.get("class") == ["Category1"]:
            categories[code] = category
        else:
            parent_category = categories[code.split(".")[0]]
            parent_category_subcategories = parent_category.get("categories", {})
            parent_category["categories"] = parent_category_subcategories | {
                code: category
            }

    return trim_dict(
        {"modifiers": modifiers, "rubric": rubric, "categories": categories}
    )


def parse_chapter_html(html_path):
    body = get_html_body(html_path)
    chapter_div = body.find("div", class_="Chapter")
    rubric = get_rubric(chapter_div)
    # ChXX modifiers are presented as 5th char but applied as 4th
    # so we have to force the . prefix to make them behave like 4th
    # downstream
    modifiers = get_modifiers(
        chapter_div, "." if "chapter-xx.htm" in str(html_path) else ""
    )
    return trim_dict({"modifiers": modifiers, "rubric": rubric})


def get_html_body(html_path):
    soup = BeautifulSoup(html_path.open(), features="html.parser")
    body = soup.body
    if not body:
        raise ValueError("Unable to parse HTML body")
    return body


def scrape():
    menu = fetch_menu_json()
    with TemporaryDirectory() as temp:
        chapters = {k: v for k, v in get_menu_chapters(menu, Path(temp))}
    return chapters
