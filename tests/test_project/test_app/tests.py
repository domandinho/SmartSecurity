from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from guardian.models import UserObjectPermission

from smart_security.smart_security import (
    SmartSecurityObjectPermissionBackend,
    SmartSecurityIncorrectConfigException,
)
from smart_security.utils import ModelOwnerPathFinder
from test_app.models import (
    TestStartModel,
    TestOwner,
    TestAnotherStartModel,
    TestBroker,
    TestOtherBroker,
)


class InspectorTests(TestCase):
    def test_simple_inspection(self):
        x = ModelOwnerPathFinder()
        self.assertEquals(
            x.find_shortest_path_to_owner_model(TestStartModel, TestOwner),
            "broker.owner",
        )
        self.assertEquals(
            x.find_shortest_path_to_owner_model(
                model_to_search_class=TestAnotherStartModel,
                security_model_class=TestOwner,
            ),
            "test.broker.owner",
        )
        self.assertEquals(
            x.find_shortest_path_to_owner_model(
                model_to_search_class=TestStartModel, security_model_class=TestBroker
            ),
            "broker",
        )
        self.assertEquals(
            x.find_shortest_path_to_owner_model(
                model_to_search_class=TestBroker, security_model_class=TestOwner
            ),
            "owner",
        )
        self.assertIsNone(
            x.find_shortest_path_to_owner_model(
                model_to_search_class=TestStartModel,
                security_model_class=TestAnotherStartModel,
            )
        )
        self.assertIsNone(
            x.find_shortest_path_to_owner_model(
                model_to_search_class=TestStartModel,
                security_model_class=TestOtherBroker,
            )
        )


class ObjectPermissionBackendTests(TestCase):
    def setUp(self):
        self.user = User.objects.create(username="jack")
        self.backend = SmartSecurityObjectPermissionBackend()
        self.owner = TestOwner.objects.create(name="owner")
        self.broker = TestBroker.objects.create(owner=self.owner)
        self.other_broker_model = TestOtherBroker.objects.create(another=self.owner)
        self.other_owner = TestOwner.objects.create(name="other")
        self.other_broker = TestOtherBroker.objects.create(another=self.other_owner)
        self.start_model = TestStartModel.objects.create(broker=self.broker)
        self.another_start_model = TestAnotherStartModel.objects.create(
            test=self.start_model
        )

    def _assert_permission_state(self, expected: bool, permission: str, instance):
        assert expected == self.backend.has_perm(self.user, permission, instance)

    def _assert_has_perm(self, permission: str, instance):
        self._assert_permission_state(
            expected=True, permission=permission, instance=instance
        )

    def _assert_has_no_perm(self, permission: str, instance):
        self._assert_permission_state(
            expected=False, permission=permission, instance=instance
        )

    def test_authenticate(self):
        self.assertEqual(
            self.backend.authenticate(
                request={}, username=self.user.username, password=self.user.password
            ),
            None,
        )

    def test_has_perm(self):
        self._assert_has_no_perm("view_testowner", self.owner)
        UserObjectPermission.objects.assign_perm(
            "view_testowner", self.user, self.owner
        )
        self.assertTrue(self.backend.has_perm(self.user, "view_testowner", self.owner))

    def test_has_perm_transitive(self):
        self._assert_has_no_perm("view_testbroker", self.broker)
        UserObjectPermission.objects.assign_perm(
            "view_testowner", self.user, self.owner
        )
        self._assert_has_perm("view_testbroker", self.broker)
        self._assert_has_perm("view_testotherbroker", self.other_broker_model)
        self._assert_has_no_perm("view_testotherbroker", self.other_broker)

    def test_has_perm_long_path(self):
        self._assert_has_no_perm("view_teststartmodel", self.start_model)
        self._assert_has_no_perm("view_testanotherstartmodel", self.another_start_model)

        UserObjectPermission.objects.assign_perm(
            "view_testowner", self.user, self.owner
        )
        self._assert_has_perm("view_teststartmodel", self.start_model)
        self._assert_has_perm("view_testanotherstartmodel", self.another_start_model)

    @override_settings(SMART_SECURITY_MODEL_CLASS=None)
    def test_no_smart_security_object_class(self):
        with self.assertRaisesRegex(
            expected_exception=SmartSecurityIncorrectConfigException,
            expected_regex="SMART_SECURITY_MODEL_CLASS setting must be different then None!",
        ):
            self._assert_has_no_perm("view_testbroker", self.broker)

    @override_settings(SMART_SECURITY_MODEL_CLASS="nonexisting_app.TestOwner")
    def test_incorrect_app_in_smart_security_object_class(self):
        with self.assertRaisesRegex(
            expected_exception=SmartSecurityIncorrectConfigException,
            expected_regex="SMART_SECURITY_MODEL_CLASS setting is wrong: "
            "No installed app with label 'nonexisting_app",
        ):
            self._assert_has_no_perm("view_testbroker", self.broker)

    @override_settings(SMART_SECURITY_MODEL_CLASS="test_app.TestOwnerXYZ")
    def test_incorrect_model_in_smart_security_object_class(self):
        with self.assertRaisesRegex(
            expected_exception=SmartSecurityIncorrectConfigException,
            expected_regex="SMART_SECURITY_MODEL_CLASS setting is wrong: App 'test_app' "
            "doesn't have a 'TestOwnerXYZ' model.",
        ):
            self._assert_has_no_perm("view_testbroker", self.broker)

    @override_settings(SMART_SECURITY_MODEL_CLASS="incorrect_config")
    def test_incorrect_smart_security_object_class(self):
        with self.assertRaisesRegex(
            expected_exception=SmartSecurityIncorrectConfigException,
            expected_regex="SMART_SECURITY_MODEL_CLASS must be app_name.model_name, "
            "current is 'incorrect_config'!",
        ):
            self._assert_has_no_perm("view_testbroker", self.broker)
