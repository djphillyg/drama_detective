from setuptools import find_packages, setup

setup(
    name="drama-detective",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "anthropic>=0.18.0",
        "click>=8.1.7",
        "rich>=13.7.0",
        "pydantic>=2.5.0",
        "python-dotenv>=1.0.0",
    ],
    entry_points={
        "console_scripts": [
            "drama=src.cli:cli",
            "drama-api=src.api_server:main",
        ],
    },
    python_requires=">=3.9",
)
