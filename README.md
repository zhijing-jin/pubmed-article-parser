This code reads the pubmed articles in xml format, then analyze the country of authors, and finally outputs the articles into two categories: native vs non-native.

## Get parsed pubmed articles
### Method 1: Download processed articles
```
python -c "from torchtext.utils import download_from_url; download_from_url('https://drive.google.com/uc?id=1newFVsPX7MHmG4O9PAM-1aDbyyC-iL5b&export=download', root='.')"
```
### Method 2: Process the files yourself
First, download the `pmc_result.xml` file at this [website](https://www.ncbi.nlm.nih.gov/pmc/?term=one) and put it under [`data/`](data/) folder.

Then, execute 
```bash
python datareader.py
```
You will get `articles_classified.csv` in your current directory.