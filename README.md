LT2OpenCorpora
==============

Python script to convert ukrainian morphological dictionary to OpenCorpora format.
Script runs well under PyPy and also collects some stats/insights/anomalies in the input dictionary.
Use at your own risk.

## Prerequisites
```pip install -r requirements.txt```

## Batteries included
* mapping.csv with general information about tagset used in ukrainian morphological dictionary. Exported (from here)[https://docs.google.com/spreadsheets/d/1CA5-11RQhlkTEVXejB9IQOwmzzBXBsH_dfKlcYQlPrU/edit#gid=1425823959].
* Excerpts (first 1000 words) from ukrainian morphological dictionary.

## Running
```python convert.py 1000.txt out.xml --debug```
