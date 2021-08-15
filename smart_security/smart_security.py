from logging import getLogger
from typing import Optional, Union, Type, List

from django.apps import apps
from django.conf import settings
from django.contrib.auth.models import User, Permission
from django.db.models import Model
from guardian.backends import ObjectPermissionBackend

from smart_security.constants import (
    SMART_SECURITY_MODEL_CLASS_SETTING,
)
from smart_security.utils import ModelOwnerPathFinder

logger = getLogger("smart_security")


class SmartSecurityIncorrectConfigException(Exception):
    pass


class SmartSecurityObjectPermissionBackend(ObjectPermissionBackend):
    def has_perm(
        self, user_obj: User, perm: Union[str, Permission], obj: Optional[Model] = None
    ) -> bool:
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
    def _find_shortest_accessor(
        cls, model_class: Type[Model], security_model_class: Type[Model]
    ) -> List[str]:
        finder = ModelOwnerPathFinder()
        shortest = finder.find_shortest_path_to_owner_model(
            model_to_search_class=model_class,
            security_model_class=security_model_class,
        )
        shortest = shortest.split(".")
        return shortest

    @classmethod
    def _get_permission_name_from_model_name(cls, model_class: Type[Model]) -> str:
        return model_class.__name__.lower()

    @classmethod
    def _get_security_model_class(cls) -> Type[Model]:
        smart_security_model_class_name = getattr(
            settings,
            SMART_SECURITY_MODEL_CLASS_SETTING,
            None,
        )
        if smart_security_model_class_name is None:
            raise SmartSecurityIncorrectConfigException(
                "SMART_SECURITY_MODEL_CLASS setting must be different then None!"
            )
        try:
            app_label, model_name = smart_security_model_class_name.rsplit(
                ".", maxsplit=1
            )
        except ValueError:
            raise SmartSecurityIncorrectConfigException(
                f"SMART_SECURITY_MODEL_CLASS must be app_name.model_name, "
                f"current is '{smart_security_model_class_name}'!"
            )
        try:
            security_model_class = apps.get_model(
                app_label=app_label, model_name=model_name
            )
        except LookupError as e:
            raise SmartSecurityIncorrectConfigException(
                f"SMART_SECURITY_MODEL_CLASS setting is wrong: {e}"
            )
        return security_model_class
