# Create your models here.
from django.db.models import (
    Model,
    ForeignKey,
    CASCADE,
    TextField,
)


class TestOwner(Model):
    name = TextField(primary_key=True)

    class Meta:
        permissions = [
            ("not_unique_permission", "Not unique permission"),
        ]


class TestBroker(Model):
    class Meta:
        permissions = [
            ("unique_permission", "Unique permission"),
            ("not_unique_permission", "Not unique permission"),
        ]

    owner = ForeignKey(TestOwner, on_delete=CASCADE)


class TestOtherBroker(Model):
    another = ForeignKey(TestOwner, on_delete=CASCADE)


class TestStartModel(Model):
    broker = ForeignKey(TestBroker, on_delete=CASCADE)


class TestAnotherStartModel(Model):
    test = ForeignKey(TestStartModel, on_delete=CASCADE)


class DummyModel(Model):
    name = TextField(primary_key=True)
