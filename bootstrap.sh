#!/bin/bash
pip install -r requirements.txt
pip install -r requirements-dev.txt

python metadata/get_races.py
python metadata/get_candidates.py
python metadata/build_metadata.py
