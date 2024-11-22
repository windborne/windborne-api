from setuptools import setup, find_packages

setup(
    name="windborne",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "requests",
        "boto3",
        "PyJWT"
    ],
    python_requires=">=3.6",
    description="A Python library for interacting with Windborne Data and Forecasts API",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="WindBorne Systems",
    author_email="data@windbornesystems.com",
    url="https://github.com/windborne/windborne-api",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
    ],
)
