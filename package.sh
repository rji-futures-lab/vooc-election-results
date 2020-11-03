#!/bin/bash
# prepare a source code package

pip install --upgrade --target package/ -r requirements.txt
cd package
zip -r9 ${OLDPWD}/package.zip .
cd ${OLDPWD}

zip -g package.zip metadata/races.csv
zip -g package.zip metadata/candidates.csv
zip -g package.zip metadata/charts.json
zip -g package.zip function.py
zip -g package.zip oc.py
zip -g package.zip sd.py
zip -g package.zip la.py
zip -g package.zip la.py
zip -g package.zip sos_ballot_measures.py
zip -g package.zip sos_candidate_races.py
zip -g package.zip graphics.py

rm -rf package