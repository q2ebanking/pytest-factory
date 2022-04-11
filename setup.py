import re
from pathlib import Path
import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()


def get_reqs():
    """Reads requirements from the pip-tools generated requirements/main.txt

    :return: Required package names
    :rtype: list
    """
    path = Path("requirements/main.txt")
    with open(path, "r") as f:
        text = f.read()
    pattern = re.compile(r"^\w.*?")
    lines = text.split("\n")
    reqs = [line.split("==")[0] for line in lines if re.search(pattern, line)]
    return reqs


setuptools.setup(
    name="pytest-factory",
    version="0.1.0",  # TODO pull from changelog
    author="Q2 Software",
    author_email="bansuki@gmail.com",
    description="pytest factories for web services",
    long_description=long_description,
    long_description_content_type="text/markdown",
    install_requires=get_reqs(),
    url="https://github.com/pytest-factory/pytest-factory",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache LICENSE-2.0",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.7',
)
