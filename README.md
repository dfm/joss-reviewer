# Find a JOSS reviewer

This script simplifies the process of choosing a JOSS reviewer given the list of volunteers, some keywords, and some programming language names.

## Usage

Optionally, set up a conda environment:

```bash
conda env create --prefix ./env -f environment.yml
conda activate ./env
```

Install the script:

```bash
python -m pip install .
```

Then run the search.
To search for reviewers with expertise in `astronomy` and `cosmology`, and experience with `Python` and `C++`, you would run something like:

```bash
joss-reviewer astronomy cosmology -l Python -l C++
```

Use `joss-reviewer --help` for all the command line options.

## GitHub interface

This script can also fetch information about potential reviewers from the GitHub API.
To enable that, create [a personal access token](https://github.com/settings/tokens) and provide it using the `GITHUB_API_KEY` environment variable.
The script should then automatically print information about the potential reviewers top repositories.
