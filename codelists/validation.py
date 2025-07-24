import operator

from django import forms

from .coding_systems import CODING_SYSTEMS


def validate_csv_data_codes(coding_system, codes):
    # Fully implemented codings systems have a `lookup_names` method that is used to
    # validate the codes in the CSV upload.  However, we also support uploads for some
    # coding systems that we don't maintain data for (e.g. OPCS4, ReadV2).  Skip code
    # validation for these systems, and just allow upload of the CSV data as it is.
    if not coding_system.has_database:
        return
    unknown_codes = set(codes) - set(coding_system.lookup_names(codes))
    unknown_codes_and_ixs = sorted(
        [(codes.index(code), code) for code in unknown_codes],
        key=operator.itemgetter(0),
    )

    if unknown_codes_and_ixs:
        line = unknown_codes_and_ixs[0][0] + 1
        code = unknown_codes_and_ixs[0][1]
        if len(unknown_codes_and_ixs) == 1:
            msg = f"CSV file contains 1 unknown code ({code}) on line {line}"
        else:
            num = len(unknown_codes_and_ixs)
            suffix = "" if num == 1 else "s"
            msg = f"CSV file contains {num} unknown code{suffix} -- the first ({code}) is on line {line}"
        msg += f" ({coding_system.short_name} release {coding_system.release_name}, valid from {coding_system.release.valid_from})"
        raise forms.ValidationError(msg)


class CSVValidationMixin:
    def decode_csv_data(self):
        try:
            return self.cleaned_data["csv_data"].read().decode("utf-8-sig")
        except UnicodeDecodeError as exception:
            raise forms.ValidationError(
                "File could not be read. Please ensure the file contains CSV "
                "data (not Excel, for example). It should be a text file encoded "
                f"in the UTF-8 format. Error details: {exception}."
            )

    def get_coding_system(self):
        # Eventually coding system version may be a selectable field, but for now it
        # just defaults to using the most recent one
        return CODING_SYSTEMS[
            self.cleaned_data["coding_system_id"]
        ].get_by_release_or_most_recent()

    def get_code_column_index(self, first_csv_row, coding_system):
        for i, value in enumerate(first_csv_row):
            if value != value.strip():
                raise forms.ValidationError(
                    f'Header {i + 1} ("{value}") contains extraneous whitespace'
                )

        # restrict the headers we expect
        possible_code_headers = {
            header.lower().strip() for header in coding_system.csv_headers["code"]
        }
        csv_headers = [header.lower().strip() for header in first_csv_row]

        code_headers = possible_code_headers & set(csv_headers)
        if not code_headers:
            raise forms.ValidationError(
                "Expected code header not found: one of {possible_code_headers} required"
            )
        if len(code_headers) > 1:
            raise forms.ValidationError(
                "Multiple possible code headers found: {code_headers}"
            )

        # TODO: validate that there's only one match?
        # Maybe rethink header handling.
        return csv_headers.index(next(iter(code_headers)))

    def get_codes_from_header_csv(self, csv_rows, code_col_ix):
        # This was the previous only existing path for
        # the `codelist/user/<name>/add` upload mechanism.
        num_columns = len(csv_rows[0])

        number_of_column_errors = []
        codes = []
        for i, row in enumerate(csv_rows[1:], start=2):
            # Ignore completely blank lines
            if not row:
                continue
            if len(row) != num_columns:
                number_of_column_errors.append(i)
            codes.append(row[code_col_ix])

        if number_of_column_errors:
            msg = "Incorrect number of columns on row {}"
            raise forms.ValidationError(
                [
                    forms.ValidationError(msg.format(i), code=f"row{i}")
                    for i in number_of_column_errors
                ]
            )

        return codes

    def get_codes_from_nonheader_csv(self, csv_rows):
        # This was the previous only existing path for "Create a codelist" upload CSV.
        # It is still used for upload page for codelists with no header.
        # It does not apply for the `codelist/user/<name>/add/` upload page.
        return [row[0] for row in csv_rows if row]

    def process_csv_data(self):
        # TODO: to make into `_clean_csv_data`
        # and call with minimum setup from `_clean_csv_data`.
        pass
