from logging import getLogger
from typing import Optional, Union, Type, List, Tuple

from django.apps import apps
from django.conf import settings
from django.contrib.auth.models import User, Permission
from django.db.models import Model
from guardian.backends import ObjectPermissionBackend
from guardian.ctypes import get_content_type

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
        perm = self._get_permission_codename(perm)
        if obj is not None:
            obj, perm = self._get_obj_and_perm(obj, perm)
        return super().has_perm(user_obj, perm, obj=obj)

    def _get_obj_and_perm(self, obj: Model, perm: str) -> Tuple[Model, str]:
        security_model_class = self._get_security_model_class()
        model_class = obj.__class__
        if security_model_class != model_class:
            owner = self._get_owner(model_class, obj, security_model_class)
            owner_perm = perm.replace(
                self._get_permission_name_from_model_name(model_class),
                self._get_permission_name_from_model_name(security_model_class),
            )
            if self._should_apply_smart_security(owner, owner_perm):
                obj = owner
                perm = owner_perm
        return obj, perm

    def _get_owner(
        self, model_class: Type[Model], obj: Model, security_model_class: Type[Model]
    ) -> Model:
        shortest = self._find_shortest_accessor(model_class, security_model_class)
        for accessor in shortest:
            obj = getattr(obj, accessor)
        return obj

    @classmethod
    def _get_permission_codename(cls, perm: Union[str, Permission]) -> str:
        if isinstance(perm, Permission):
            return perm.codename
        return perm

    @classmethod
    def _should_apply_smart_security(cls, owner: Model, owner_perm: str) -> bool:
        content_type = get_content_type(owner)
        return Permission.objects.filter(
            codename=owner_perm, content_type=content_type
        ).exists()

    @classmethod
    def _find_shortest_accessor(
        cls, model_class: Type[Model], security_model_class: Type[Model]
    ) -> List[str]:
        finder = ModelOwnerPathFinder()
        shortest = finder.find_shortest_path_to_owner_model(
            model_to_search_class=model_class,
            security_model_class=security_model_class,
        )
        if shortest is not None:
            accessors_sequence = shortest.split(".")
        else:
            accessors_sequence = []
        return accessors_sequence

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
