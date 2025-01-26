from setuptools import setup


setup(
    # Python Package name should be identical on PyPI
    # Note that PyPI is case-insensitive
    name="envkp",
    version='0.0.1',
    install_requires=['setuptools'],    # httpx, requests, ...etc
    entry_points={
        "console_scripts": [
            "envkp = envkp.core:cli",
            # with adding, we can use multiple entries as CLI such as `envkp` & `envkp-dump`
            # "envkp-dump = envkp.core:dump",
        ]
    }
)
