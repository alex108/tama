import io
import re

from setuptools import setup, find_packages

with io.open("README.md", "rt", encoding="utf8") as f:
    readme = f.read()

with io.open("src/tama/__init__.py", "rt", encoding="utf8") as f:
    version = re.search(r"__version__ = \"(.*?)\"", f.read()).group(1)

install_requires = [
    "aiodns>=2.0",
    "aiohttp>=3.6",
    "brotlipy>=0.7",
    "cchardet>=2.1",
    "toml>=0.10",
]

setup(
    name="tama",
    author="Alex",
    author_email="alex@meido.ninja",
    description="IRC bot.",
    long_description=readme,
    version=version,
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    include_package_data=True,
    zip_safe=False,
    python_requires=">=3.8",
    install_requires=install_requires,
)
