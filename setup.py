from distutils.core import setup

setup(
    name="Smart Security",
    version="2.0",
    description=(
        "Extension of django-guardian to allow "
        "delegate permission checking to owner model."
    ),
    packages=["smart_security"],
    python_requires=">=3.5",
    author="Piotr Domański",
    author_email="piotrjerzydomanski@gmail.com",
)
