from django import forms

from .coding_systems import CODING_SYSTEMS


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

        return csv_headers.index(next(iter(code_headers)))

    def get_codes_from_header_csv(self, csv_rows, code_col_ix):
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
        return [row[0] for row in csv_rows if row]
