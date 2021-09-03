from distutils.core import setup

setup(
    name="Smart Security",
    version="2.0",
    description=(
        "Extension of django-guardian to allow "
        "delegate permission checking to owner model."
    ),
    packages=["smart_security"],
    python_requires=">=3.6",
    author="Piotr Domański",
    author_email="piotrjerzydomanski@gmail.com",
    classifiers=[
        "Environment :: Web Environment",
        "Framework :: Django",
        "Framework :: Django :: 2.2",
        "Framework :: Django :: 3.0",
        "Framework :: Django :: 3.1",
        "Framework :: Django :: 3.2",
        "Programming Language :: Python",
        "Topic :: Security",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
    ],
)
