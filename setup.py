from distutils.core import setup

setup(
      name='Smart Security',
      version='2.0',
      description=(
            "Extension of django-guardian to allow "
            "check permissions recursively based on models"
      ),
      author='Piotr Domanski',
      author_email='piotrjerzydomanski@gmail.com',
      packages=['smart_security'],
)
