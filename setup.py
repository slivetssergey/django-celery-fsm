#!/usr/bin/env python

"""The setup script."""

from setuptools import find_packages, setup

with open("README.md") as readme_file:
    readme = readme_file.read()

requirements = []

test_requirements = ["pytest>=3"]

setup(
    author="Sergey Slivets",
    author_email="slivetssergey@gmail.com",
    python_requires=">=3.7",
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
    ],
    description="Django FSM with Celery tasks as step handler",
    install_requires=requirements,
    license="License :: OSI Approved :: MIT License",
    long_description=readme,
    include_package_data=True,
    keywords="django-celery-fsm",
    name="django-celery-fsm",
    packages=find_packages(include=["django_celery_fsm", "django_celery_fsm.*"]),
    test_suite="tests",
    tests_require=test_requirements,
    url="https://github.com/slivetssergey/django-celery-fsm",
    version="0.0.1-rc.1",
    zip_safe=False,
)
