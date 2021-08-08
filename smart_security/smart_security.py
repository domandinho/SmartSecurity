from logging import getLogger

from django.apps import apps
from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from guardian.backends import ObjectPermissionBackend

from smart_security.constants import (
    META_ATTRIBUTE,
    IGNORE_SMART_SECURITY_OPTION,
    SMART_SECURITY_MODEL_CLASS_SETTING,
)
from smart_security.utils import ModelOwnerPathFinder

logger = getLogger("smart_security")


class SmartSecurity:
    """
    A Smart Security class is a highly customizable tool to avoid writing
    many similar decorators, and passing lot of them in every methods
    responsible for handling requests.
    A user should define a owner's model.
    Id's of elements of this model should be accessible from request variable.
    Than this library can check (for any argument of a
    decorated method) whether has user permission to this object.
    """

    @classmethod
    def ignore_check(cls, model_class):
        """
        This decorator is used for determine, which models should not
        be checked.
        @param model_class: model class for which permission check
        should be skipped
        @return: this model with changed metadata
        """
        model_class._meta.ignore_smart_security = True
        return model_class

    @classmethod
    def if_user_has_no_permissions(cls, request, key, value):
        """
        This method determines what to do if user hasn't
        permissions to requested object.
        @param request:
        @param key: name of an argument
        @param value: id of an model element
        @return:
        """
        raise PermissionDenied()

    @classmethod
    def get_owner_id_from_request(cls, request):
        """
        An accessor to the the owner id.
        @param request:
        @return: owner's id
        """
        return request.user

    @classmethod
    def get_owner_class(cls):
        """
        An accessor to owner's model
        @return: owner's model
        """
        return User

    @classmethod
    def _should_model_be_checked(cls, model):
        return (
            hasattr(model, META_ATTRIBUTE)
            and hasattr(model._meta, IGNORE_SMART_SECURITY_OPTION)
            and model._meta.ignore_smart_security
        )

    @classmethod
    def get_all_models_candidates(cls):
        """
        A method to select all models which can be checked.
        @return: list of models
        """
        all_models = apps.get_models()
        return [model for model in all_models if cls._should_model_be_checked(model)]


class SmartSecurityObjectPermissionBackend(ObjectPermissionBackend):
    def has_perm(self, user_obj, perm, obj=None):
        if obj is not None:
            security_model_class = self._get_security_model_class()
            model_class = obj.__class__
            if security_model_class != model_class:
                shortest = self._find_shortest_accessor(
                    model_class, security_model_class
                )
                for accessor in shortest:
                    obj = getattr(obj, accessor)
                perm = perm.replace(
                    self._get_permission_name_from_model_name(model_class),
                    self._get_permission_name_from_model_name(security_model_class),
                )
        return super().has_perm(user_obj, perm, obj=obj)

    @classmethod
    def _find_shortest_accessor(cls, model_class, security_model_class):
        finder = ModelOwnerPathFinder()
        shortest = finder.find_shortest_path_to_owner_model(
            model_to_search_class=model_class,
            security_model_class=security_model_class,
        )
        shortest = shortest.split(".")
        return shortest

    @classmethod
    def _get_permission_name_from_model_name(cls, model_class):
        return model_class.__name__.lower()

    @classmethod
    def _get_security_model_class(cls):
        app_label, model_name = getattr(
            settings,
            SMART_SECURITY_MODEL_CLASS_SETTING,
            None,  # TODO: raise exception if absent
        ).rsplit(".", maxsplit=1)
        security_model_class = apps.get_model(
            app_label=app_label, model_name=model_name
        )
        return security_model_class
