from unittest import TestCase

from django.db.models import Model, ForeignKey, IntegerField, OneToOneField, ManyToManyField

from smart_security import replace_with_defaults, ModelOwnerPathFinder, SmartSecurity


class _SampleClassForTestDecorator(object):
    def __init__(self, **kwargs):
        super(_SampleClassForTestDecorator, self).__init__()
        for key, value in kwargs.items():
            setattr(self, "default_" + key, value)

    @replace_with_defaults
    def first(self, key=42):
        return key

    @replace_with_defaults
    def second(self, key=42, value=42):
        return key, value

    @replace_with_defaults
    def third(self, p=42):
        return p


class TestModelMixin(object):
    class Meta:
        app_label = 'Test application'


class _TestOwner(Model, TestModelMixin):
    name = IntegerField()


class _TestOtherBroker(Model, TestModelMixin):
    another = ForeignKey(_TestOwner)


class _TestBroker(Model, TestModelMixin):
    owner = ForeignKey(_TestOwner)


class _TestStartModel(Model, TestModelMixin):
    broker = ForeignKey(_TestBroker)


class _TestAnotherStartModel(Model, TestModelMixin):
    test = ForeignKey(_TestStartModel)


class _TestOneToOneStartModel(Model, TestModelMixin):
    one = OneToOneField(_TestStartModel)


class _TestManyToManyStartModel(Model, TestModelMixin):
    many = ManyToManyField(_TestOneToOneStartModel)


class InspectorTests(TestCase):
    def test_simple_method(self):
        x = _SampleClassForTestDecorator(key=13, value=34)
        self.assertEquals(x.first(), 13)
        self.assertEquals(x.first(key=111), 111)
        self.assertEquals(x.second(value=88), (13, 88))
        self.assertEquals(x.second(key=22, value=88), (22, 88))
        self.assertEquals(x.second(key=161), (161, 34))
        self.assertEquals(x.second(), (13, 34))
        self.assertEquals(x.third(p=3), 3)
        self.assertEquals(x.third(), 42)

    def test_defaults_with_passing_kwargs_using_position(self):
        x = _SampleClassForTestDecorator(key=13, value=34)
        self.assertEquals(x.second(22, 33), (22, 33))
        self.assertEquals(x.first(555), 555)
        self.assertEquals(x.third(555), 555)

    def test_simple_inspection(self):
        x = ModelOwnerPathFinder(_TestStartModel, _TestOwner)
        self.assertEquals(x.find_shortest_path_to_owner_model(), 'broker__owner')
        self.assertEquals(x.find_shortest_path_to_owner_model(model_to_search_class=_TestAnotherStartModel),
                          'test__broker__owner')
        self.assertEquals(x.find_shortest_path_to_owner_model(security_model_class=_TestBroker),
                          'broker')
        self.assertEquals(x.find_shortest_path_to_owner_model(model_to_search_class=_TestOtherBroker),
                          'another')
        self.assertEquals(x.find_shortest_path_to_owner_model(model_to_search_class=_TestOneToOneStartModel),
                          'one__broker__owner')
        self.assertEquals(x.find_shortest_path_to_owner_model(model_to_search_class=_TestManyToManyStartModel),
                          'many__one__broker__owner')
        self.assertIsNone(x.find_shortest_path_to_owner_model(security_model_class=_TestAnotherStartModel))
        self.assertIsNone(x.find_shortest_path_to_owner_model(security_model_class=_TestOtherBroker))


class DecoratorTest(TestCase):
    def test_converting_names(self):
        self.assertEquals("SampleModel", SmartSecurity._convert_variable_to_class_name("sample_model_id"))
        self.assertEquals("LongSampleModel", SmartSecurity._convert_variable_to_class_name("long_sample_model_id"))
        self.assertEquals("Sample", SmartSecurity._convert_variable_to_class_name("sample_id"))

    _typical_answer = [('b', 1), ('a', 6)]

    def test_merging_arguments(self):
        self.assertEquals(self._typical_answer, SmartSecurity._merge_args_and_kwargs(lambda b, a=9: a, [1], {'a': 6}))
        self.assertEquals([('b', 8), ('a', 6)],
                          SmartSecurity._merge_args_and_kwargs(lambda b=8, a=9: a, [], {'a': 6, 'b': 8}))
        self.assertEquals([], SmartSecurity._merge_args_and_kwargs(lambda: 1, [], {}))
        self.assertEquals([('b', 1), ('a', 2)], SmartSecurity._merge_args_and_kwargs(lambda b, a: b, [1, 2], []))
        self.assertEquals([('c', 3), ('b', 1), ('d', 2), ('a', 0)], SmartSecurity._merge_args_and_kwargs(
                lambda c, b, d=5, a=5: c, [3, 1], {'a': 0, 'd': 2}))

    def test_strange_args_as_kwargs(self):
        self.assertEquals(self._typical_answer, SmartSecurity._merge_args_and_kwargs(lambda b, a=9: a, [1, 6], {}))
        self.assertEquals(self._typical_answer, SmartSecurity._merge_args_and_kwargs(lambda b=4, a=9: a, [1, 6], {}))

    def test_strange_kwargs_as_args(self):
        self.assertEquals(self._typical_answer,
                          SmartSecurity._merge_args_and_kwargs(lambda b, a: a, [], {'a': 6, 'b': 1}))
        self.assertEquals(self._typical_answer,
                          SmartSecurity._merge_args_and_kwargs(lambda b, a=3: a, [], {'a': 6, 'b': 1}))
