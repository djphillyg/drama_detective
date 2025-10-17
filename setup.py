from setuptools import setup, find_packages

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
            "drama=drama_detective.cli:cli",
        ],
    },
    python_requires=">=3.9",
)