import functools

from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.apps import apps
from logging import getLogger

from smart_security.constants import (
    META_ATTRIBUTE,
    IGNORE_SMART_SECURITY_OPTION,
    SHOULD_BE_CHECKED_ATTRIBUTE_SUFFIX,
    ID_SUFFIX_REGEX,
)
from smart_security.utils import get_function_spec, ModelOwnerPathFinder, is_integer
import re

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
    def check_permissions(cls, function):
        """
        A decorator which retrieves arguments from method.
        For each argument with a name matching to pattern <model_name>_id
        he finds a way to owner's class
        and compares owner's id with an id from request.
        @param function: function to decorate
        @return: decorated function
        """

        @functools.wraps(function)
        def inner(request, *args, **kwargs):
            owner_id = cls.get_owner_id_from_request(request)
            merged_arguments = cls._merge_args_and_kwargs(
                function, (request,) + args, kwargs
            )
            finder = ModelOwnerPathFinder(None, cls.get_owner_class())
            for key, value in merged_arguments:
                model_class = cls.get_model_for_argument(key)
                if model_class is None or not is_integer(value):
                    continue
                    # If name of an argument doesn't match to any existing
                    # model than checking is continued.
                has_user_access = finder.detect_has_user_object_access(
                    int(value), owner_id, model_to_search_class=model_class
                )
                if not has_user_access:
                    cls.if_user_has_no_permissions(request, key, value)

            return function(request, *args, **kwargs)

        return inner

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

    @classmethod
    def get_model_for_argument(cls, key):
        """
        An argument to model matcher.
        @param key: name of an argument
        @return: a model class if it exists of None otherwise
        """
        if not key.endswith(SHOULD_BE_CHECKED_ATTRIBUTE_SUFFIX):
            return None
        model_classes = cls._get_model_classes(key)
        if not model_classes:
            return None
        elif len(model_classes) > 1:
            module = model_classes[0].__module__
            logger.warning(
                f"Many models with the same name: {key}. "
                f"First matching model from module {module} was chosen."
            )
        return model_classes[0]

    @classmethod
    def _get_model_classes(cls, key):
        all_models = cls.get_all_models_candidates()
        key_as_model_name = cls._convert_variable_to_class_name(key)
        model_classes = [
            model for model in all_models if model.__name__ == key_as_model_name
        ]
        return model_classes

    @classmethod
    def _convert_variable_to_class_name(cls, variable_name):
        # This method converts argument names
        # (like "some_model_id" to class names (like "SomeModel")
        variable_name = re.sub(ID_SUFFIX_REGEX, "", variable_name)
        result = ""
        for element in variable_name.split("_"):
            if len(element) >= 1:
                result += element[0].upper() + element[1:]
        return result

    @classmethod
    def _merge_args_and_kwargs(
        cls, function, positional_arguments_to_merge, key_value_arguments_to_merge
    ):
        # This method creates a list of all arguments of a function with their values
        argument_names, defaults = get_function_spec(function)
        key_value_arguments_with_defaults = cls._get_key_value_arguments_with_defaults(
            argument_names=argument_names,
            defaults=defaults,
        )
        key_value_arguments_with_defaults.update(key_value_arguments_to_merge)
        result = list(zip(argument_names, positional_arguments_to_merge))
        number_of_positional_arguments = len(result)
        for argument_name in argument_names[number_of_positional_arguments:]:
            result.append(
                (argument_name, key_value_arguments_with_defaults[argument_name])
            )
        return result

    @classmethod
    def _get_key_value_arguments_with_defaults(cls, argument_names, defaults):
        number_of_arguments = len(argument_names)
        arguments_offset = number_of_arguments - len(defaults)
        key_value_arguments_names = argument_names[arguments_offset:]
        key_value_arguments_with_defaults = dict(
            zip(key_value_arguments_names, defaults)
        )
        return key_value_arguments_with_defaults
