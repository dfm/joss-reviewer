from setuptools import setup
from pathlib import Path  # noqa E402

CURRENT_DIR = Path(__file__).parent


def get_long_description() -> str:
    readme_md = CURRENT_DIR / "README.md"
    with open(readme_md, encoding="utf8") as ld_file:
        return ld_file.read()


setup(
    name="joss_reviewer",
    use_scm_version=True,
    description="Find reviewers for JOSS",
    long_description=get_long_description(),
    long_description_content_type="text/markdown",
    author="Dan Foreman-Mackey",
    author_email="foreman.mackey@gmail.com",
    url="https://github.com/dfm/joss-reviewer",
    license="MIT",
    py_modules=["joss_reviewer"],
    python_requires=">=3.6",
    zip_safe=False,
    install_requires=["requests", "numpy", "pandas"],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3 :: Only",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    entry_points={"console_scripts": ["joss-reviewer=joss_reviewer:main"]},
)
