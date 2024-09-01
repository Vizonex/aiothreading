from setuptools import setup, find_packages
from aiothreading import __version__, __author__
import pathlib



def main():
    try:
        long_description = (pathlib.Path("aiothreading").parent / "readme.md").open("r").read()
    except Exception:
        long_description = ""

    setup(
        name="aiothreading",
        author=__author__,
        version=__version__,
        packages=find_packages(),
        include_package_data=True,
        description="AsyncIO version of the standard threading module",
        long_description=long_description,
        long_description_content_type="text/markdown",
        keywords=["aiothreading", "threading", "asyncio"],
        classifiers=[
            "Development Status :: 4 - Beta",
            "Framework :: AsyncIO",
            "Intended Audience :: Developers",
            "Topic :: Software Development :: Libraries",
            "Programming Language :: Python :: 3.8",
            "Programming Language :: Python :: 3.9",
            "Programming Language :: Python :: 3.10",
            "Programming Language :: Python :: 3.11",
            "Programming Language :: Python :: 3.12",
        ]
    )

if __name__ == "__main__":
    main()

