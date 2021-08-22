from distutils.core import setup

setup(
    name="Smart Security",
    version="2.0",
    description=(
        "Extension of django-guardian to allow "
        "delegate permission checking to owner model."
    ),
    author="Piotr Domański",
    author_email="piotrjerzydomanski@gmail.com",
    packages=["smart_security"],
)
