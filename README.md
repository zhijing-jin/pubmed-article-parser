This code reads the pubmed articles in xml format, then analyze the country of authors, and finally outputs the articles into two categories: native vs non-native.

## Get Started
First, download the `pmc_result.xml` file at this [website](https://www.ncbi.nlm.nih.gov/pmc/?term=one) and put it under [`data/`](data/) folder.

Then, execute 
```bash
python preprocess.py
```