# Create your models here.
from django.db.models import (
    Model,
    ForeignKey,
    CASCADE,
    TextField,
)


class TestOwner(Model):
    name = TextField(primary_key=True)


class TestBroker(Model):
    owner = ForeignKey(TestOwner, on_delete=CASCADE)


class TestOtherBroker(Model):
    another = ForeignKey(TestOwner, on_delete=CASCADE)


class TestStartModel(Model):
    broker = ForeignKey(TestBroker, on_delete=CASCADE)


class TestAnotherStartModel(Model):
    test = ForeignKey(TestStartModel, on_delete=CASCADE)
