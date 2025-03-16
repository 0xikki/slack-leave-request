from setuptools import setup, find_packages

setup(
    name="slack-leave-system",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "flask>=3.0.2",
        "slack-sdk>=3.27.1",
        "gunicorn>=21.2.0",
        "python-dotenv>=1.0.1",
        "python-json-logger>=2.0.7",
    ],
) 