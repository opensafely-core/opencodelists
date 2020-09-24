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
            from_codes = {m[from_coding_system_id] for m in mappings}
            to_codes = {m[to_coding_system_id] for m in mappings}

            from_coding_system_lookup_names = from_coding_system.lookup_names(
                from_codes
            )
            to_coding_system_lookup_names = to_coding_system.lookup_names(to_codes)

            if form.cleaned_data["type"] == "full":
                filename = f"{base_filename}-mapping.csv"
                headers = [
                    f"{from_coding_system_id}_id",
                    f"{from_coding_system_id}_name",
                    f"{to_coding_system_id}_id",
                    f"{to_coding_system_id}_name",
                ]
                data = [
                    [
                        mapping[from_coding_system_id],
                        from_coding_system_lookup_names.get(
                            mapping[from_coding_system_id], "Unknown"
                        ),
                        mapping[to_coding_system_id],
                        to_coding_system_lookup_names.get(
                            mapping[to_coding_system_id], "Unknown"
                        ),
                    ]
                    for mapping in mappings
                ]
            else:
                filename = f"{base_filename}-{to_coding_system_id}.csv"
                headers = [
                    f"{to_coding_system_id}_id",
                    f"{to_coding_system_id}_name",
                ]
                data = [
                    [to_code, to_coding_system_lookup_names.get(to_code, "Unknown")]
                    for to_code in to_codes
                ]

            response = HttpResponse(content_type="text/csv")
            response["Content-Disposition"] = f'attachment; filename="{filename}"'
            writer = csv.writer(response)
            writer.writerow(headers)
            writer.writerows(sorted(data))

            return response

    else:
        form = ConvertForm()

    ctx = {"form": form}
    return render(request, "conversions/convert.html", ctx)
