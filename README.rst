.. image:: https://github.com/domandinho/SmartSecurity/actions/workflows/tests.yml/badge.svg?branch=master
  :target: https://github.com/django-guardian/django-guardian/actions/workflows/tests.yml
.. image:: https://github.com/domandinho/SmartSecurity/actions/workflows/black.yml/badge.svg?branch=master
  :target: https://github.com/domandinho/SmartSecurity/actions/workflows/black.yml/badge.svg
.. image:: https://github.com/domandinho/SmartSecurity/actions/workflows/linting.yml/badge.svg?branch=master
  :target: https://github.com/domandinho/SmartSecurity/actions/workflows/linting.yml/badge.svg
.. image:: https://github.com/domandinho/SmartSecurity/actions/workflows/mypy.yml/badge.svg?branch=master
  :target: https://github.com/domandinho/SmartSecurity/actions/workflows/mypy.yml/badge.svg
.. image:: https://github.com/domandinho/SmartSecurity/actions/workflows/coverage.yml/badge.svg?branch=master
  :target: https://github.com/domandinho/SmartSecurity/actions/workflows/coverage.yml/badge.svg

``SmartSecurity`` is an extension of django-guardian package, which allows to delegate object's
permissions checking into foreign object called OwnerObject.
When object is connected in database to owner object by sequence of relationships
than permissions checking can be delegated into the owner object.
This allows to optimize memory usage of database as instead of granting every user access to every
entity within some namespace, we can just grant it into the owner object.

Implementation
--------------
Under the hood SmartSecurity is loading model graphs and looking for the shortest path to the owner model using the BFS algorithm.

Requirements
------------
* Python 3.8+
* django-guardian >= 2.0

Configuration
-------------

We need to hook ``django-guardian`` into our project.


1. Add extra authorization backend ``SmartSecurityObjectPermissionBackend`` to your ``settings.py``:

.. code:: python

    AUTHENTICATION_BACKENDS = (
        'django.contrib.auth.backends.ModelBackend', # default
        'guardian.backends.ObjectPermissionBackend',
        'smart_security.smart_security.SmartSecurityObjectPermissionBackend',
    )

2. Configure ``SMART_SECURITY_MODEL_CLASS`` in django settings.py::

     SMART_SECURITY_MODEL_CLASS = "sample_app.SampleOwner"
