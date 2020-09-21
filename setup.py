import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="pytest-factory",
    version="0.1.0",
    author="Q2 Software",
    author_email="bansuki@gmail.com",
    description="pytest factories for web services",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ludocracy/pytest_factory",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache LICENSE-2.0",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.7',
)
