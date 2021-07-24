import functools
from inspect import getfullargspec

from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.db.models import ManyToManyField


def _get_function_spec(function):
    argspec = getfullargspec(function)
    arguments = argspec.args
    defaults = argspec.defaults or ()
    return arguments, defaults


def replace_with_defaults(function):
    """
    A decorator to inserting default values from an self object into a method.
    @param function: function to decorate
    @return: decorated function
    """

    @functools.wraps(function)
    def inner(self, *args, **kwargs):
        default_marker = "default_"
        arguments, defaults = _get_function_spec(function)
        index_of_first_kwarg_not_passed_using_position = max(
            len(args) + 1, len(arguments) - len(defaults)
        )
        for key_value_argument in arguments[
            index_of_first_kwarg_not_passed_using_position:
        ]:
            # Adding to kwargs defaults from self
            if key_value_argument not in kwargs and hasattr(
                self, default_marker + key_value_argument
            ):
                kwargs[key_value_argument] = getattr(
                    self, default_marker + key_value_argument
                )
        return function(self, *args, **kwargs)

    return inner


class SmartSecurity(object):
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
            merged_arguments = SmartSecurity._merge_args_and_kwargs(
                function, (request,) + args, kwargs
            )
            finder = ModelOwnerPathFinder(None, cls.get_owner_class())
            for key, value in merged_arguments:
                model_class = cls.get_model_for_argument(key)
                if model_class is None or not SmartSecurity._is_integer(value):
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
    def get_all_models_candidates(cls):
        """
        A method to select all models which can be checked.
        @return: list of models
        """
        from django.apps import apps

        def should_not_be_checked(model):
            return not (
                hasattr(model, "_meta")
                and hasattr(model._meta, "ignore_smart_security")
                and model._meta.ignore_smart_security
            )

        all_models = apps.get_models()
        return filter(should_not_be_checked, all_models)

    @classmethod
    def get_model_for_argument(cls, key):
        """
        An argument to model matcher.
        @param key: name of an argument
        @return: a model class if it exists of None otherwise
        """
        from logging import getLogger

        should_be_checked_suffix = "_id"
        if not key.endswith(should_be_checked_suffix):
            return None
        all_models = cls.get_all_models_candidates()
        key_as_model_name = SmartSecurity._convert_variable_to_class_name(key)
        model_classes = [
            model for model in all_models if model.__name__ == key_as_model_name
        ]
        number_of_models_matching_criteria = len(model_classes)
        if number_of_models_matching_criteria == 0:
            return None
        elif number_of_models_matching_criteria > 1:
            getLogger("django.request").warning(
                """
            Many models with the same name: {0}."\n
            First matching model from module {1} was chosen.
            """.format(
                    key, model_classes[0].__module__
                )
            )
        return model_classes[0]

    @staticmethod
    def _convert_variable_to_class_name(variable_name):
        # This method converts argument names
        # (like "some_model_id" to class names (like "SomeModel")
        import re

        variable_name = re.sub("_id$", "", variable_name)
        result = ""
        for element in variable_name.split("_"):
            if len(element) >= 1:
                result += element[0].upper() + element[1:]
        return result

    @staticmethod
    def _is_integer(integer_candidate):
        try:
            int(integer_candidate)
            return True
        except (ValueError, TypeError):
            return False

    @staticmethod
    def _merge_args_and_kwargs(
        function, positional_arguments_to_merge, key_value_arguments_to_merge
    ):
        # This method creates a list of all
        # arguments of a function with their values
        argument_names, defaults = _get_function_spec(function)
        number_of_arguments = len(argument_names)
        arguments_offset = number_of_arguments - len(defaults)
        key_value_arguments_names = argument_names[arguments_offset:]
        key_value_arguments_with_defaults = dict(
            zip(key_value_arguments_names, defaults)
        )
        key_value_arguments_with_defaults.update(key_value_arguments_to_merge)
        result = list(zip(argument_names, positional_arguments_to_merge))
        number_of_positional_arguments = len(result)
        for argument_name in argument_names[number_of_positional_arguments:]:
            result.append(
                (argument_name, key_value_arguments_with_defaults[argument_name])
            )
        return result


def smart_security_decorator(
    check_permissions=None,
    if_user_has_no_permissions=None,
    get_owner_id_from_request=None,
    get_owner_class=None,
    get_all_models_candidates=None,
    get_model_for_argument=None,
):
    """A decorator which work exactly the same as classes derived
    from SmartSecurity.
    He requires that all arguments must be functions with class instance
    as first parameter.
    @param check_permissions:
    @param if_user_has_no_permissions:
    @param get_owner_id_from_request:
    @param get_owner_class:
    @param get_all_models_candidates:
    @param get_model_for_argument:
    @return: a check_persmissions decorator from dynamically created class
    """

    methods_to_override = [
        ("check_permissions", check_permissions),
        ("if_user_has_no_permissions", if_user_has_no_permissions),
        ("get_owner_id_from_request", get_owner_id_from_request),
        ("get_owner_class", get_owner_class),
        ("get_all_models_candidates", get_all_models_candidates),
        ("get_model_for_argument", get_model_for_argument),
    ]
    methods_to_override = filter(lambda x: x[1] is not None, methods_to_override)
    methods_to_override_as_class_methods = map(
        lambda method: (method[0], classmethod(method[1])), methods_to_override
    )
    new_type = type(
        "SmartSecurityAnonymousClass",
        (SmartSecurity,),
        dict(methods_to_override_as_class_methods),
    )
    return new_type.check_permissions


class ModelOwnerPathFinder(object):
    """
    This class is responsible for finding the
    shortest path to the owner's model.
    An application can be treated as a graph.
    Models are vertexes and relationships are edges.
    """

    def __init__(self, default_model_to_search_class, default_security_model_class):
        super(ModelOwnerPathFinder, self).__init__()
        self.default_model_to_search_class = default_model_to_search_class
        self.default_security_model_class = default_security_model_class

    @replace_with_defaults
    def find_shortest_path_to_owner_model(
        self, model_to_search_class=None, security_model_class=None
    ):
        """
        A method to investigate the shortest path to owner's class
        @param model_to_search_class: a model to investigate path
        @param security_model_class: a owner's class
        @return: a path to the owner's class
        """
        from collections import deque
        from django.db.models.fields.related import ForeignKey, OneToOneField

        ancestors = {}

        def process_ancestors():
            # This method creates argument name to access
            # owner's class from model manager of model_to_search_class
            result = ""
            current_element = security_model_class
            field_delimiter = "__"
            while current_element != model_to_search_class:
                current_element, foreign_key_field = ancestors[current_element]
                result = foreign_key_field.name + field_delimiter + result
            return result[: -len(field_delimiter)]

        queue_of_models = deque()
        queue_of_models.append(model_to_search_class)
        while len(queue_of_models):
            # An BFS algorithm to find the shortest path to owner's class.
            current_class = queue_of_models.popleft()
            if current_class == security_model_class:
                return process_ancestors()
            fields_and_many_to_many_relations = (
                current_class._meta.fields + current_class._meta.many_to_many
            )
            for field in fields_and_many_to_many_relations:
                relation_fields = (
                    ForeignKey,
                    OneToOneField,
                    ManyToManyField,
                )
                if (
                    isinstance(field, relation_fields)
                    and not field.null
                    and field.related_model not in ancestors
                ):
                    next_class = field.related_model
                    ancestors[next_class] = (current_class, field)
                    queue_of_models.append(next_class)

    @replace_with_defaults
    def detect_has_user_object_access(
        self,
        model_id,
        owner_id,
        model_to_search_class=None,
        security_model_class=None,
    ):
        """
        A method to check has user access to model_id.
        @param model_id: id of model instance
        @param owner_id: id of owner instance
        @param model_to_search_class:
        @param security_model_class:
        @return: True if element belongs to owner or false otherwise
        """
        shortest_path_to_owner = self.find_shortest_path_to_owner_model(
            model_to_search_class=model_to_search_class,
            security_model_class=security_model_class,
        )
        return (
            shortest_path_to_owner is None
            or model_to_search_class.objects.filter(
                **{"pk": model_id, shortest_path_to_owner: owner_id}
            ).exists()
        )
