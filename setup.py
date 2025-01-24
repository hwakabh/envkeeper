from setuptools import setup # find_packages


setup(
    name="envkeeper",
    # packages=find_packages(),
    install_requires=[],    # httpx, requests, ...etc
    entry_points={
        "console_scripts": [
            "envkp = envkeeper.core:cli",
            "envkp-dump = envkeeper.core:dump",
        ]
    }
)
