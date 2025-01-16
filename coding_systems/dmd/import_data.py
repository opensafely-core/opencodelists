from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZipFile

import structlog
from django.db import connections
from django.db.models import fields as django_fields
from lxml import etree
from tqdm import tqdm

from codelists.models import CodelistVersion
from coding_systems.base.import_data_utils import CodingSystemImporter
from coding_systems.dmd import models
from mappings.dmdvmpprevmap.models import Mapping

from .data_downloader import Downloader


logger = structlog.get_logger()


def import_data(
    release_dir,
    release_name,
    valid_from,
    latest=False,
    import_ref=None,
    check_compatibility=True,
):
    downloader = Downloader(release_dir)
    release_zipfile_path = downloader.download_release(release_name, valid_from, latest)
    import_release(
        release_zipfile_path, release_name, valid_from, import_ref, check_compatibility
    )


def import_release(
    release_zipfile_path,
    release_name,
    valid_from,
    import_ref=None,
    check_compatibility=True,
):
    import_ref = import_ref or release_zipfile_path.name

    with TemporaryDirectory() as tempdir:
        release_zip = ZipFile(str(release_zipfile_path))
        logger.info("Extracting", release_zip=release_zip.filename)
        release_zip.extractall(path=tempdir)

        inner_zip = Path(tempdir).glob("*.zip")
        for inner_zipfile in inner_zip:
            ZipFile(inner_zipfile).extractall(path=tempdir)

        with CodingSystemImporter(
            "dmd", release_name, valid_from, import_ref, check_compatibility
        ) as database_alias:
            import_coding_system(Path(tempdir), database_alias)

    update_vmp_prev_mapping(database_alias)
    update_cached_download_data()


def import_coding_system(release_dir, database_alias):
    # dm+d data is provided in several XML files:
    #
    # * f_amp2_3[ddmmyy].xml
    # * f_ampp2_3[ddmmyy].xml
    # * f_gtin2_0[ddmmyy].xml
    # * f_ingredient2_3[ddmmyy].xml
    # * f_lookup2_3[ddmmyy].xml
    # * f_vmp2_3[ddmmyy].xml
    # * f_vmpp2_3[ddmmyy].xml
    # * f_vtm2_3[ddmmyy].xml
    #
    # Each file contains a list or lists of elements that correspond to
    # instances of one of the models in models.py.
    #
    # Each such element has the structure:
    #
    # <OBJ_TYPE>
    #   <FIELD1>value</FIELD1>
    #   <FIELD2>value</FIELD2>
    #   <FIELD3>value</FIELD3>
    # </OBJ_TYPE>
    #
    # These elements are arranged differently in different files.
    #
    # The ingredient and VTM files just contain a list of elements
    # corresponding to instances of Ing and VTM respectively.  For
    # instance:
    #
    # <INGREDIENT_SUBSTANCES>
    #     <!-- Generated by NHSBSA PPD -->
    #     <ING>...</ING>
    #     <ING>...</ING>
    #     ...
    # </INGREDIENT_SUBSTANCES>
    #
    # The VMP, VMPP, AMP, AMPP and lookup files contain several lists of
    # elements, corresponding to multiple types of objects.  For instance:
    #
    # <VIRTUAL_MED_PRODUCTS>
    #     <!-- Generated by NHSBSA PPD -->
    #     <VMPS>
    #         <VMP>...</VMP>
    #         <VMP>...</VMP>
    #         ...
    #     </VMPS>
    #     <VIRTUAL_PRODUCT_INGREDIENT>
    #         <VPI>...</VPI>
    #         <VPI>...</VPI>
    #         ...
    #     </VIRTUAL_PRODUCT_INGREDIENT>
    #     <ONT_DRUG_FORM>
    #         <ONT>...</ONT>
    #         <ONT>...</ONT>
    #         ...
    #     </ONT_DRUG_FORM>
    #     ...
    # <VIRTUAL_MED_PRODUCTS>
    #
    # The GTIN file is a bit weird and the data requires a little massaging
    # before it can be imported.  See code below.
    #
    # Since the data model contains foreign key constraints, the order we
    # import the files is significant.
    #
    # When importing the data, we first delete all existing instances,
    # because the IDs of some SNOMED objects can change.

    # Retrieve the full filepath for each expected XML file first
    # Some of the models take a long time to load, this means we can check the
    # expected files are there before we attempt to import all the data from each one.
    file_fragments = [
        "lookup",
        "ingredient",
        "vtm",
        "vmp",
        "vmpp",
        "amp",
        "ampp",
        "gtin",
    ]
    filepaths = {
        fragment: get_filepath(release_dir, fragment) for fragment in file_fragments
    }

    # lookup
    for elements in load_elements(filepaths["lookup"]):
        model_name = make_model_name(elements.tag)
        model = getattr(models, model_name)
        import_model(model, elements, database_alias)

    # ingredient
    elements = load_elements(filepaths["ingredient"])
    import_model(models.Ing, elements, database_alias)

    # vtm
    elements = load_elements(filepaths["vtm"])
    import_model(models.VTM, elements, database_alias)

    # vmp
    for elements in load_elements(filepaths["vmp"]):
        model_name = make_model_name(elements[0].tag)
        model = getattr(models, model_name)
        import_model(model, elements, database_alias)

    # vmpp
    for elements in load_elements(filepaths["vmpp"]):
        if elements[0].tag == "CCONTENT":
            # We don't yet handle the CCONTENT tag, which indicates that a
            # VMPP is part of a combination pack, where two VMPPs are
            # always prescribed together.
            continue

        model_name = make_model_name(elements[0].tag)
        model = getattr(models, model_name)
        import_model(model, elements, database_alias)

    # amp
    for elements in load_elements(filepaths["amp"]):
        if len(elements) == 0:
            # For test data, some lists of elements are empty (eg
            # AP_INFORMATION), and so we can't look at the first element of
            # the list to get the name of the corresponding model.
            continue

        model_name = make_model_name(elements[0].tag)
        model = getattr(models, model_name)
        import_model(model, elements, database_alias)

    # ampp
    for elements in load_elements(filepaths["ampp"]):
        if len(elements) == 0:
            # For test data, some lists of elements are empty (eg
            # APPLIANCE_PACK_INFO), and so we can't look at the first
            # element of the list to get the name of the corresponding
            # model.
            continue

        if elements[0].tag == "CCONTENT":
            # We don't yet handle the CCONTENT tag, which indicates that a
            # AMPP is part of a combination pack, where two AMPPs are
            # always prescribed together.
            continue

        model_name = make_model_name(elements[0].tag)
        model = getattr(models, model_name)
        import_model(model, elements, database_alias)

    # gtin
    elements = next(load_elements(filepaths["gtin"]))
    for element in elements:
        assert element[0].tag == "AMPPID", (
            f"Expected AMPPID as first element, got {element[0].tag}"
        )
        assert element[1].tag == "GTINDATA", (
            f"Expected GTINDATA as second element, got {element[1].tag}"
        )

        element[0].tag = "APPID"
        for gtinelt in element[1]:
            element.append(gtinelt)
        element.remove(element[1])
    import_model(models.GTIN, elements, database_alias)


def get_filepath(release_dir, filename_fragment):
    paths = list(release_dir.glob(f"f_{filename_fragment}2_*.xml"))
    assert len(paths) == 1, (
        f"Expected 1 path for {f'f_{filename_fragment}2_*.xml'}, found {len(paths)}"
    )
    return paths[0]


def load_elements(filepath):
    """Return list of non-comment top-level elements in given file."""

    logger.info("Reading file", file=filepath)
    doc = etree.parse(filepath)
    root = doc.getroot()
    iterelements = root.iterchildren()
    first_element = next(iterelements)

    assert isinstance(first_element, etree._Comment), (
        f"Expected etree._Comment first row, got {type(first_element)}"
    )
    yield from iterelements


def import_model(model, elements, database):
    """Import model instances from list of XML elements."""

    # ensure the starting db is empty
    assert not model.objects.using(database).exists(), f"Expected empty db for {model}"

    boolean_field_names = [
        f.name for f in model._meta.fields if isinstance(f, django_fields.BooleanField)
    ]

    table_name = model._meta.db_table
    column_names = [
        f.db_column or f.name
        for f in model._meta.fields
        if not isinstance(f, django_fields.AutoField)
    ]
    sql = "INSERT INTO {} ({}) VALUES ({})".format(
        table_name, ", ".join(column_names), ", ".join(["%s"] * len(column_names))
    )

    logger.info("Loading model", model=model.__name__)

    def iter_values(elements):
        for element in elements:
            row = {}

            for field_element in element:
                name = field_element.tag.lower()
                if name == "desc":
                    # "desc" is a really unhelpful field name if you're writing
                    # SQL!
                    name = "descr"
                elif name == "dnd":
                    # For consistency with the rest of the data, we rename
                    # "dnd" to "dndcd", as it is a foreign key field.
                    name = "dndcd"

                value = field_element.text
                row[name] = value

            for name in boolean_field_names:
                row[name] = name in row
            yield [row.get(name) for name in column_names]

    with connections[database].cursor() as cursor:
        cursor.executemany(sql, iter_values(elements))


def make_model_name(tag_name):
    """Construct name of Django model from XML tag name."""

    if tag_name in ["VTM", "VPI", "VMP", "VMPP", "AMP", "AMPP", "GTIN"]:
        return tag_name
    else:
        return "".join(tok.title() for tok in tag_name.split("_"))


def update_vmp_prev_mapping(database_alias):
    vmps_with_prev = models.VMP.objects.using(database_alias).filter(
        vpidprev__isnull=False
    )
    for vmp in tqdm(
        vmps_with_prev,
        total=vmps_with_prev.count(),
        desc="Update VMP previous mapping",
    ):
        Mapping.objects.get_or_create(id=vmp.id, vpidprev=vmp.vpidprev)


def update_cached_download_data():
    """
    Refresh the cached_csv_data by calling csv_data_shas for each non-draft dmd
    CodelistVersion. This will also cache the default download data.
    """
    logger.info("Updating cached download data")
    for codelist_version in tqdm(
        CodelistVersion.objects.filter(codelist__coding_system_id="dmd").exclude(
            status="draft"
        )
    ):
        if codelist_version.downloadable:
            codelist_version.csv_data_shas()
