from setuptools import setup


setup(
    # Python Package name should be identical on PyPI
    # Note that PyPI is case-insensitive
    name="envkp",
    version='0.0.1',
    install_requires=['setuptools'],    # httpx, requests, ...etc
    entry_points={
        "console_scripts": [
            # we can use as CLI with the name `envkp` & `envkp-dump`
            "envkp = envkp.core:cli",
            "envkp-dump = envkp.core:dump",
        ]
    }
)
