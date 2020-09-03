import pytest
from django.core.exceptions import ValidationError

from ..forms import UserPasswordForm


def test_userpasswordform_different_passwords():
    form = UserPasswordForm()

    form.cleaned_data = {
        "new_password1": "test",
        "new_password2": "foo",
    }

    with pytest.raises(ValidationError) as e:
        form.clean_new_password2()

    assert len(e.value.messages) == 1
    assert e.value.messages[0] == "The two password fields don't match."
