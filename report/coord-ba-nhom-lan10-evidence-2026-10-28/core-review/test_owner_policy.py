"""New owner policy received after the original 23-pass contract review.

The existing synthetic fixture creates its first and only admin before any
learner; this account is the bootstrap admin in this counterexample.
"""
import pytest

from test_independent_admin import case, snapshot
from wayfinder.application.accounts import AuthError


def test_new_owner_policy_first_admin_cannot_be_disabled(case):
    before = snapshot(case)
    with pytest.raises(AuthError):
        case.service.update_user(case.admin,case.admin.user_id,{'status':'disabled'})
    assert snapshot(case) == before
