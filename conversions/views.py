import csv
import os
from collections import defaultdict
from io import StringIO

from django.http import HttpResponse
from django.views.generic.edit import FormView

from codelists.coding_systems import CODING_SYSTEMS
from mappings.ctv3sctmap2.mappers import get_mappings

from .forms import ConvertForm


class ConvertView(FormView):
    template_name = "conversions/convert.html"
    form_class = ConvertForm

    def form_valid(self, form):
        from_coding_system_id = form.cleaned_data["from_coding_system_id"]
        to_coding_system_id = form.cleaned_data["to_coding_system_id"]
        assert from_coding_system_id != to_coding_system_id
        from_coding_system = CODING_SYSTEMS[from_coding_system_id]
        to_coding_system = CODING_SYSTEMS[to_coding_system_id]

        base_filename, _ = os.path.splitext(form.cleaned_data["csv_data"].name)
        csv_data = form.cleaned_data["csv_data"].read().decode("utf-8-sig")

        from_codes = [row[0] for row in csv.reader(StringIO(csv_data))]
        kwargs = {"include_unassured": form.cleaned_data["include_unassured"]}
        if from_coding_system_id == "snomedct":
            assert to_coding_system_id == "ctv3"
            kwargs["snomedct_ids"] = from_codes
        else:
            assert from_coding_system_id == "ctv3"
            assert to_coding_system_id == "snomedct"
            kwargs["ctv3_ids"] = from_codes

        mappings = get_mappings(**kwargs)

        if form.cleaned_data["type"] == "full":
            return _build_csv_response_for_full_mapping(
                base_filename,
                mappings,
                from_coding_system,
                to_coding_system,
            )
        else:
            return _build_csv_response_for_converted_codes_only(
                base_filename,
                mappings,
                to_coding_system,
            )


def _build_csv_response_for_full_mapping(
    base_filename,
    mappings,
    from_coding_system,
    to_coding_system,
):

    # For each pair of (from_code, to_code) in the mappings, work out whether there are
    # any mappings that are assured.
    pair_to_is_assureds = defaultdict(set)
    for m in mappings:
        from_code = m[from_coding_system.id]
        to_code = m[to_coding_system.id]
        pair_to_is_assureds[(from_code, to_code)].add(m["is_assured"])
    pair_to_is_assured = {
        pair: True in is_assureds for pair, is_assureds in pair_to_is_assureds.items()
    }

    from_codes = {m[from_coding_system.id] for m in mappings}
    to_codes = {m[to_coding_system.id] for m in mappings}
    from_coding_system_lookup_names = from_coding_system.lookup_names(from_codes)
    to_coding_system_lookup_names = to_coding_system.lookup_names(to_codes)

    filename = f"{base_filename}-mapping.csv"
    headers = [
        f"{from_coding_system.id}_id",
        f"{from_coding_system.id}_name",
        f"{to_coding_system.id}_id",
        f"{to_coding_system.id}_name",
        "is_assured",
    ]
    data = [
        [
            from_code,
            from_coding_system_lookup_names[from_code],
            to_code,
            to_coding_system_lookup_names[to_code],
            is_assured,
        ]
        for (from_code, to_code), is_assured in pair_to_is_assured.items()
    ]

    return _build_csv_response(filename, headers, data)


def _build_csv_response_for_converted_codes_only(
    base_filename, mappings, to_coding_system
):

    # For each to_code in the mappings, work out whether there are any mappings that are
    # assured.
    code_to_is_assureds = defaultdict(set)
    for m in mappings:
        code_to_is_assureds[m[to_coding_system.id]].add(m["is_assured"])
    code_to_is_assured = {
        code: True in is_assureds for code, is_assureds in code_to_is_assureds.items()
    }
    to_coding_system_lookup_names = to_coding_system.lookup_names(code_to_is_assured)

    filename = f"{base_filename}-{to_coding_system.id}.csv"
    headers = [
        f"{to_coding_system.id}_id",
        f"{to_coding_system.id}_name",
        "is_assured",
    ]
    data = [
        [code, to_coding_system_lookup_names.get(code, "Unknown"), is_assured]
        for code, is_assured in code_to_is_assured.items()
    ]

    return _build_csv_response(filename, headers, data)


def _build_csv_response(filename, headers, data):
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    writer = csv.writer(response)
    writer.writerow(headers)
    writer.writerows(sorted(data))
    return response
