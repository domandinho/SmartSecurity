from django.db import models

# Create your models here.
from django.db.models import Model, IntegerField, ForeignKey, OneToOneField, \
    ManyToManyField, CASCADE


class TestModelMixin(object):
    class Meta:
        app_label = 'Test application'


class _TestOwner(Model, TestModelMixin):
    name = IntegerField()


class _TestOtherBroker(Model, TestModelMixin):
    another = ForeignKey(_TestOwner, on_delete=CASCADE)


class _TestBroker(Model, TestModelMixin):
    owner = ForeignKey(_TestOwner, on_delete=CASCADE)


class _TestStartModel(Model, TestModelMixin):
    broker = ForeignKey(_TestBroker, on_delete=CASCADE)


class _TestAnotherStartModel(Model, TestModelMixin):
    test = ForeignKey(_TestStartModel, on_delete=CASCADE)


class _TestOneToOneStartModel(Model, TestModelMixin):
    one = OneToOneField(_TestStartModel, on_delete=CASCADE)


class _TestManyToManyStartModel(Model, TestModelMixin):
    many = ManyToManyField(_TestOneToOneStartModel)

