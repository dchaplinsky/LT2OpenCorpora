LT2OpenCorpora
==============

Python script to convert ukrainian morphological dictionary from LanguageTool project to OpenCorpora format.
Script runs well under PyPy and also collects some stats/insights/anomalies in the input dictionary.
Use at your own risk.

It solves these tasks:
* Parses LanguageTool raw dictionary format
* Performs some basic sanity checks (and collects some stats about input dict)
* Converts LanguageTool tags to OpenCorpora tags
* Groups together wordforms and tries to determine a lemma for the group
* Exports tagset, tagset restrictions and all the lemmas to OpenCorpora format. 

## It's all about grouping
Grouping wordforms under particular lemma is cumbersome for various reasons. Mostly because of homonymy and internal format of LanguageTool dict.
In short:
* Entry in LanugageTool dictionary looks like this `wordform tag1:tag2:tag3 lemma`, where lemma is just a string.
* You cannot tell, to which lemma exactly this entry refers because of homonymy.
* So you can only apply a bunch of heuristics: lemma should have the same POS as wordform also, lemma should have particular tags. For example, for nouns all lemmas should have :v_naz tag.
* Another problem with heuristic is that a lot of verb lemmas looks the same for :perf and :imperf tags. But those are two different lemmas and they have their own wordforms!

## Prerequisites
```pip install -r requirements.txt```

## Batteries included
* mapping.csv with general information about tagset used in ukrainian morphological dictionary. Exported [from here](https://docs.google.com/spreadsheets/d/1CA5-11RQhlkTEVXejB9IQOwmzzBXBsH_dfKlcYQlPrU/edit#gid=1425823959).
* Excerpt (first 1000 words) from ukrainian morphological dictionary.

## Visualised mapping between tagsets in a great detail
![Mapping](http://i.imgur.com/qiP2HSl.png)
* Cream nodes are for tags found only in OpenCorpora
* Blue nodes are for tags from LanguageTool only
* Green nodes are for tags that can be found in both
* LT tag name is on top
* OpenCorpora tag name is on bottom
* Blue links are for OpenCorpora
* Orange links are for LT

## Running
```python convert.py 1000.txt out.xml --debug```
