from datetime import date

from django.conf import settings
from django.utils import six
from django.utils.crypto import constant_time_compare, salted_hmac
from django.utils.http import int_to_base36, base36_to_int
from django.utils.timezone import now, localtime


class BaseTokenGenerator(object):
    """
    Strategy object used to generate and check tokens based on model
    state.

    """
    key_salt = "brambling.BaseTokenGenerator"

    def make_token(self, instance):
        return self._make_token_with_timestamp(instance,
                                               self._num_days(self._today()))

    def check_token(self, instance, token):
        """
        Check that a token is correct for a given instance.

        """
        # Parse the token
        try:
            nd_b36, hash = token.split("-")
        except ValueError:
            return False

        try:
            nd = base36_to_int(nd_b36)
        except ValueError:
            return False

        # Check that the num_days/uid has not been tampered with
        if not constant_time_compare(self._make_token_with_timestamp(instance, nd), token):
            return False

        # Check the num_days is within limit
        if (self._num_days(self._today()) - nd) > self._timeout_days():
            return False

        return True

    def _make_token_with_timestamp(self, instance, num_days):
        # num_days is number of days since 2001-1-1.  Converted to
        # base 36, this gives us a 3 digit string until about 2121
        nd_b36 = int_to_base36(num_days)

        # By hashing on the internal state of the instance and using state
        # that is sure to change (must be implemented by subclasses), we
        # can produce a hash that only works for this instance and will be
        # invalid as soon as it is used.
        # We limit the hash to 20 chars to keep URL short.
        default_state = (
            instance._meta.app_label,
            instance._meta.model_name,
            six.text_type(instance.pk),
            six.text_type(num_days)
        )
        value = u"".join(default_state + tuple(self._instance_state(instance)))

        hash = salted_hmac(self.key_salt, value).hexdigest()[::2]
        return "%s-%s" % (nd_b36, hash)

    def _num_days(self, dt):
        return (dt - date(2001, 1, 1)).days

    def _today(self):
        # Used for mocking in tests
        return localtime(now()).date()

    def _timeout_days(self):
        # Default to just using the password reset timeout for all tokens.
        return settings.PASSWORD_RESET_TIMEOUT_DAYS

    def _instance_state(self, instance):
        # Subclasses must return a list of state that changes once the token
        # is used.
        raise NotImplementedError


class EmailConfirmTokenGenerator(BaseTokenGenerator):
    """
    Strategy object used to generate and check tokens for the email
    confirmation mechanism.
    """
    key_salt = "brambling.tokens.EmailConfirmTokenGenerator"

    def _instance_state(self, instance):
        return (instance.email, instance.confirmed_email,)


token_generators = {
    'email_confirm': EmailConfirmTokenGenerator(),
}
