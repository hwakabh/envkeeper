from setuptools import setup # find_packages


setup(
    name="runtimop",
    # packages=find_packages(),
    install_requires=[],    # httpx, requests, ...etc
    entry_points={
        "console_scripts": [
            "envkp = runtimop.core:cli",
            "envkp-dump = runtimop.core:dump",
        ]
    }
)
