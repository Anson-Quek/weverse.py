import re

from setuptools import find_packages, setup


with open("README.md", "r") as f:
    long_description = f.read()

with open("weverse/__init__.py") as f:
    version = (
        re.search(
            r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]', f.read(), re.MULTILINE
        ).group(1)
        or ""
    )


def parse_requirements(filename):
    """Load requirements from a requirement file."""
    line_iter = (line.strip() for line in open(filename))
    return [line for line in line_iter if line and not line.startswith("#")]


setup(
    name="Weverse.py",
    author="Anson Quek",
    url="https://github.com/Anson-Quek/Weverse.py",
    version=version,
    packages=find_packages(),
    license="MIT",
    description="Weverse.py seeks to provide developers with a tool that "
    "allows them to make a bot that is able to retrieve Weverse Posts in "
    "semi real-time with relative ease.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    install_requires=parse_requirements("requirements.txt"),
    python_requires=">=3.10",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "License :: OSI Approved :: MIT License",
        "Intended Audience :: Developers",
        "Natural Language :: English",
        "Programming Language :: Python :: 3.10",
    ],
)
