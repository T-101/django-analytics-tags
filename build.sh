#!/bin/sh
set -eu

cd "$(dirname "$0")"

if [ ! -d .venv ]; then
    python3 -m venv .venv
fi
. .venv/bin/activate

python3 -m pip install --upgrade build twine

# Keep old releases out of the upload glob.
rm -f dist/*.whl dist/*.tar.gz
python3 -m build
python3 -m twine check dist/*

printf '\nActivate the virtual environment first: . .venv/bin/activate\n\n'
echo "Upload to TestPyPi: python3 -m twine upload --repository testpypi dist/*"
printf "Upload to PyPi: python3 -m twine upload dist/*\n\n"
