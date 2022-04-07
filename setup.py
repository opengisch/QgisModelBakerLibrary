import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("VERSION", "r", encoding="utf-8") as fh:
    version = fh.read().strip()

setuptools.setup(
    name="modelbaker",
    version=version,
    author="Dave Signer",
    author_email="david@opengis.ch",
    description="The full model baker core",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/opengisch/QgisModelBakerLibrary",
    classifiers=[
        "Topic :: Database",
        "License :: OSI Approved :: GNU General Public License v2 or later (GPLv2+)",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
    packages=setuptools.find_packages(exclude=["tests"]),
)
