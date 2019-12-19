# Find a JOSS reviewer

This script simplifies the process of choosing a JOSS reviewer given the list of volunteers, some keywords, and some programming language names.

## Usage

Set up your conda environment:

```bash
conda env create --prefix ./env -f environment.yml
conda activate ./env
```

Then run the search.
To search for reviewers with expertise in `astronomy` and `cosmology`, and experience with `Python` and `C++`, you would run something like:

```bash
python find_reviewer.py astronomy cosmology -l Python -l C++
```

Use `python find_reviewer.py --help` for all the command line options.