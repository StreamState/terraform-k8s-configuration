from setuptools import setup, find_packages
import os

thisFolder = os.path.dirname(os.path.realpath(__file__))
with open(os.path.abspath(os.path.join(thisFolder, "VERSION"))) as version_file:
    version = version_file.read().strip()

setup(
    name="streamstate",
    version=version,
    packages=find_packages(),
    long_description=open("README.md").read(),
    setup_requires=["pytest-runner"],
    # tests_require=["pytest"],
)