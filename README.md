LT2OpenCorpora
==============

Python script to convert the Ukrainian morphological dictionary from the LanguageTool project to the OpenCorpora format.
The script runs well under PyPy and also collects some stats/insights/anomalies in the input dictionary.
Use at your own risk.

It solves these tasks:
* Parses the LanguageTool raw dictionary format
* Performs some basic sanity checks (and collects some stats about input dict)
* Converts LanguageTool tags to OpenCorpora tags
* Groups together wordforms and tries to determine a lemma for the group
* Exports the tagset, the tagset restrictions and all lemmas to the OpenCorpora format

## It's all about grouping
Grouping wordforms under a particular lemma is cumbersome for various reasons. Mostly because of homonymy and the internal format of the LanguageTool dict.
In a nutshell:
* An entry in the LanugageTool dictionary looks like this `wordform tag1:tag2:tag3 lemma`, where lemma is just a string.
* You cannot tell, to which lemma exactly this entry refers because of homonymy.
* So, you can only apply a bunch of heuristics: the lemma should have the same POS as the wordform, the lemma should have particular tags. For example, for nouns all lemmas should have the :v_naz tag.
* Another problem with heuristics is that a lot of verb lemmas look the same for the :perf and :imperf tags. But those are two different lemmas and they have their own wordforms!

## Prerequisites
```pip install -r requirements.txt```

## Batteries included
* mapping.csv with the general information about the tagset used in the Ukrainian morphological dictionary. Exported [from here](https://docs.google.com/spreadsheets/d/1CA5-11RQhlkTEVXejB9IQOwmzzBXBsH_dfKlcYQlPrU/edit#gid=1425823959).
* An excerpt (first 1000 words) from the Ukrainian morphological dictionary.

## Visualised mapping between the tagsets in a great detail
![Mapping](http://i.imgur.com/XNdliU3.png)
* Cream nodes are for the tags found only in OpenCorpora
* Blue nodes are for the tags from LanguageTool only
* Green nodes are for the tags that can be found in both
* The LT tag name is above
* The OpenCorpora tag name is below
* Blue links are for OpenCorpora
* Orange links are for LT

## Running
```python convert.py 1000.txt out.xml --debug```
