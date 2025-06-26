"""Setup configuration for Atlas Email."""

from setuptools import setup, find_packages

setup(
    name="atlas-email",
    version="0.1.0",
    description="Professional email management system with ML-powered spam filtering",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="Atlas Engineering",
    author_email="atlas@example.com",
    url="https://github.com/atlas/atlas-email",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.11",
    install_requires=[
        # Dependencies will be listed in requirements.txt
    ],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    entry_points={
        "console_scripts": [
            "atlas-email=atlas_email.cli.main:main",
            "atlas-email-web=atlas_email.api.app:run_server",
        ],
    },
)