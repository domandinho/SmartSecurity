# Bored with writing many similar decorators?
Consider the following example:

```python
class Owner(Model):
     ...

class Model1(Model):
    owner = ForeignKey(Owner)

class Model2(Model):
    model_1 = ForeignKey(Model1)

class Model3(Model):
    model_1 = ForeignKey(Model1)

...

class ModelK(Model)
    model_<X> = ForeignKey(Model<X>)
    model_<Y> = ForeignKey(Model<Y>)
    model_<Z> = ForeignKey(Model<Z>)
```

So for each model, you need to write one decorator to detect has user permissions this object.

```python
def has_user_permissions_to_model_x(function)
    @functools.wraps(function)
    def inner(request, *args, **kwargs):
        if model_x_id in kwargs:
            if not ModelX.objects.filter(pk=model_x_id, 
                <path_to_owner_class>=request.user.something.else).exists():
                raise PermissionDenied()
    return inner
```

Additionally for each method, you need to attach correct decorators.

```python
@has_user_permissions_to_model_x
@has_user_permissions_to_model_y
@has_user_permissions_to_model_z
...
def process_request_1(model_<x>_id, model_<y>_id, ... model_<z>_id):

@has_user_permissions_to_model_x
@has_user_permissions_to_model_y
@has_user_permissions_to_model_z
...
def process_request_2(model_<x>_id, model_<y>_id, ... model_<z>_id):

...

@has_user_permissions_to_model_x
@has_user_permissions_to_model_y
@has_user_permissions_to_model_z
...
def process_request_n(model_<x>_id, model_<y>_id, ... model_<z>_id):
```

And what there are K owners? Than you must do this job k-times.

# Forget about it!!!

```bash
git clone https://github.com/pd346901/SmartSecurity.git 
pip install ./SmartSecurity/dist/Smart\ Security-1.0.tar.gz
```

```python
# Extend the base SmartSecurity class:
from smart_security.smart_security import SmartSecurity

class MySecurity(SmartSecurity):
    # Define a owner class
    @classmethod
    def get_owner_class(cls):
        return Company

    # Define method to retrieve owner's id from request.
    @classmethod
    def get_owner_id_from_request(cls, request):
        return request.user.person.company.pk
        
    # You can also redefine many others methods to customize your decorator.
```

After that you don't have to remember:
- how access owner's id for each model instance.
- how retrieve user id from request.
- which decorators use to check permissions for **ALL parameters of ALL methods**.

Now you need only append one line to each method:

```python
@MySecurity.check_permissions
```

You don't have to care about arguments and models.

What when you change database structure?

Without this library **you need to edit ALL decorators**.

With this library **you don't have to do anything**.
