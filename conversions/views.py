import csv
import os
from io import StringIO

from django.http import HttpResponse
from django.shortcuts import render

from codelists.coding_systems import CODING_SYSTEMS
from mappings.ctv3sctmap2.mappers import get_mappings

from .forms import ConvertForm


def convert(request):
    if request.POST:
        form = ConvertForm(request.POST, request.FILES)
        if form.is_valid():
            from_coding_system_id = form.cleaned_data["from_coding_system_id"]
            to_coding_system_id = form.cleaned_data["to_coding_system_id"]
            assert from_coding_system_id == "snomedct"
            assert to_coding_system_id == "ctv3"
            from_coding_system = CODING_SYSTEMS[from_coding_system_id]
            to_coding_system = CODING_SYSTEMS[to_coding_system_id]

            base_filename, _ = os.path.splitext(form.cleaned_data["csv_data"].name)
            csv_data = form.cleaned_data["csv_data"].read().decode("utf-8-sig")
            rows = list(csv.reader(StringIO(csv_data)))
            snomedct_ids = [row[0] for row in rows[1:]]
            mappings = get_mappings(snomedct_ids=snomedct_ids)

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

    else:
        form = ConvertForm()

    ctx = {"form": form}
    return render(request, "conversions/convert.html", ctx)


def _build_csv_response_for_full_mapping(
    base_filename,
    mappings,
    from_coding_system,
    to_coding_system,
):
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
    ]
    data = [
        [
            mapping[from_coding_system.id],
            from_coding_system_lookup_names.get(
                mapping[from_coding_system.id], "Unknown"
            ),
            mapping[to_coding_system.id],
            to_coding_system_lookup_names.get(mapping[to_coding_system.id], "Unknown"),
        ]
        for mapping in mappings
    ]

    return _build_csv_response(filename, headers, data)


def _build_csv_response_for_converted_codes_only(
    base_filename, mappings, to_coding_system
):
    to_codes = {m[to_coding_system.id] for m in mappings}
    to_coding_system_lookup_names = to_coding_system.lookup_names(to_codes)

    filename = f"{base_filename}-{to_coding_system.id}.csv"
    headers = [
        f"{to_coding_system.id}_id",
        f"{to_coding_system.id}_name",
    ]
    data = [
        [to_code, to_coding_system_lookup_names.get(to_code, "Unknown")]
        for to_code in to_codes
    ]

    return _build_csv_response(filename, headers, data)


def _build_csv_response(filename, headers, data):
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    writer = csv.writer(response)
    writer.writerow(headers)
    writer.writerows(sorted(data))
    return response
