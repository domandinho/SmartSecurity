from collections import deque
from typing import Type, Deque, Tuple, Dict, Optional

from django.db.models import Model
from django.db.models.fields.related import ForeignKey


class ModelOwnerPathFinder:
    """
    This class is responsible for finding the
    shortest path to the owner's model.
    An application can be treated as a graph.
    Models are vertexes and relationships are edges.
    """

    def find_shortest_path_to_owner_model(
        self,
        model_to_search_class: Type[Model],
        security_model_class: Type[Model],
    ) -> Optional[str]:
        """
        A method to investigate the shortest path to owner's class
        @param model_to_search_class: a model to investigate path
        @param security_model_class: a owner's class
        @return: a path to the owner's class
        """

        bfs_search = BFSModelSearch(
            model_to_search_class=model_to_search_class,
            security_model_class=security_model_class,
        )
        return bfs_search.search()


ANCESTORS_DICT = Dict[Type[Model], Tuple[Type[Model], ForeignKey]]


class BFSModelSearch:
    def __init__(
        self, model_to_search_class: Type[Model], security_model_class: Type[Model]
    ):
        self._model_to_search_class = model_to_search_class
        self._security_model_class = security_model_class

    def search(self) -> Optional[str]:
        ancestors: ANCESTORS_DICT = {}

        queue_of_models: Deque[Type[Model]] = deque()
        queue_of_models.append(self._model_to_search_class)
        while len(queue_of_models):
            # An BFS algorithm to find the shortest path to owner's class.
            current_class = queue_of_models.popleft()
            if current_class == self._security_model_class:
                return self._process_ancestors(ancestors)
            self._process_current_class(ancestors, current_class, queue_of_models)
        return None

    @classmethod
    def _process_current_class(
        cls,
        ancestors: ANCESTORS_DICT,
        current_class: Type[Model],
        queue_of_models: Deque,
    ):
        meta_data = current_class._meta
        fields_and_many_to_many_relations = meta_data.fields + meta_data.many_to_many
        for field in fields_and_many_to_many_relations:
            relation_fields = (ForeignKey,)
            if (
                isinstance(field, relation_fields)
                and not field.null
                and field.related_model not in ancestors
            ):
                next_class = field.related_model
                ancestors[next_class] = (current_class, field)
                queue_of_models.append(next_class)

    def _process_ancestors(self, ancestors: ANCESTORS_DICT) -> str:
        # This method creates argument name to access
        # owner's class from model manager of model_to_search_class
        result = ""
        current_element = self._security_model_class
        field_delimiter = "."
        while current_element != self._model_to_search_class:
            current_element, foreign_key_field = ancestors[current_element]
            result = foreign_key_field.name + field_delimiter + result
        return result[: -len(field_delimiter)]
