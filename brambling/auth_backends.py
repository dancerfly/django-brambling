from brambling.models import (
    Organization,
    OrganizationMember,
    Event,
    EventMember,
)


class BramblingBackend(object):
    """
    Handles object-based permissions for brambling models.

    """
    def authenticate(self, **kwargs):
        pass

    def get_user(self, user_id):
        pass

    def get_all_permissions(self, user_obj, obj=None):
        if obj is None:
            return set()

        if not user_obj.is_authenticated() or not user_obj.is_active:
            return set()

        if not hasattr(user_obj, '_brambling_perm_cache'):
            user_obj._brambling_perm_cache = {}
        perm_cache = user_obj._brambling_perm_cache

        cls_name = obj.__class__.__name__
        if cls_name not in perm_cache:
            perm_cache[cls_name] = {}

        if obj.pk not in perm_cache[cls_name]:
            perm_cache[cls_name][obj.pk] = set(obj.get_permissions(user_obj))

        return perm_cache[cls_name][obj.pk]

    def has_perm(self, user_obj, perm, obj=None):
        return perm in self.get_all_permissions(user_obj, obj)
