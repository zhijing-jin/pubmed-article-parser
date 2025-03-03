def check_env():
    try:
        import tqdm
        import lxml
        import requests
        import selenium
        import spacy
        import xmltodict
        import efficiency
        import email2country
    except:
        import os
        os.system(
            'pip install tqdm xmltodict lxml spacy efficiency ted_talk_downloader')


# check_env()
from email2country import EmailCountryChecker


class Dataset:
    def __init__(self, files, use_all_secs=True, save_to=1):
        import pickle
        from efficiency.log import show_time

        show_time('[Info] files: {}, use_all_secs:{}, save_to:{}'
                  .format(files, use_all_secs, save_to))

        with open('articles{}.pickle'.format(save_to), 'rb') as f:
            self.articles = pickle.load(f)

        # self.articles = []
        # for file in files:
        #     doc = self.load_file(file)
        #     self.articles += self.parse(doc, file, use_all_secs=use_all_secs)
        # print('[Info] {} articles'.format(len(self.articles)))
        # self.save('articles{}.pickle'.format(save_to))
        # self.save_ids('pmids{}.txt'.format(save_to))

        self.filter_by_ids()
        self.articles_non_native, self.articles_native = \
            self.split_by_nation()
        txt_native = self.get_txt(self.articles_native,
                                  'articles_native{}.txt'.format(save_to))
        txt_non_native = self.get_txt(self.articles_non_native,
                                      'articles_non_native{}.txt'.format(
                                          save_to))
        import pdb;pdb.set_trace()
        txt_native, txt_non_native, eval_native, eval_non_native = \
            self.postprocess_txt(txt_native, txt_non_native)

        self.save_csv(txt_native, txt_non_native,
                      file='articles_classified{}.csv'.format(save_to))
        self.save_csv(eval_native, eval_non_native,
                      file='articles_eval{}.csv'.format(save_to))
        self.run_classifier(file='articles_classified{}.csv'.format(save_to))

    @staticmethod
    def load_file(file):
        from lxml import etree
        from efficiency.log import show_time

        show_time('[Info] Loading file in')
        doc = etree.parse(file)
        show_time('[Info] Finished loading file in')

        return doc

    def save(self, file):
        import pickle

        with open(file, 'wb') as handle:
            pickle.dump(self.articles, handle, protocol=pickle.HIGHEST_PROTOCOL)

    def save_ids(self, file):
        from efficiency.log import fwrite
        pmids = [a.data['pmid'] for a in self.articles]
        fwrite('\n'.join(pmids), file)

    def filter_by_ids(self):
        with open('pmids2.txt') as f:
            prev_ids = {line.strip() for line in f if line.strip()} - {'None'}
        self.articles = list(filter(lambda a: a.data['pmid'] not in prev_ids, self.articles))

    @staticmethod
    def parse(doc, file, use_all_secs=True):
        from tqdm import tqdm

        articles = []
        pbar = tqdm(doc.iter('article'))
        pbar.set_description('Parsing Articles from ' + file)
        for article in pbar:
            if not (article.xpath('.//front//contrib-group')
                    and article.xpath('.//body')):
                continue

            a = Article()
            a.lxml2json(article, use_all_secs=use_all_secs)

            articles.append(a)
        return articles

    def split_by_nation(self):
        from tqdm import tqdm

        country_checker = CountryChecker()
        en = country_checker.english_speaking_countries
        if_native = lambda x: not (x - (en | {None}))
        # if_native = lambda x: x == {'United States'}
        # if_non_native = lambda x: not (x & en)
        if_non_native = lambda x: x == {'China'}
        if_useless = lambda x: (not x)  # or (None in x)

        articles_non_native = []
        articles_native = []

        pbar = tqdm(self.articles, desc='Got 0 valid countries')

        for article in pbar:
            countries = article.set_countries(country_checker)
            # item = (article.data['countries'], article.data['affs'])
            if if_useless(countries): continue # articles_non_native.append(article)
            elif if_native(countries):
                articles_native.append(article)
            elif if_non_native(countries):
                articles_non_native.append(article)

            total_len = len(articles_non_native) + len(articles_native)
            pbar.set_description('Got {} valid countries'.format(total_len),
                                 refresh=True)

        return articles_non_native, articles_native

    @staticmethod
    def get_txt(articles, file='articles_native.txt'):
        from tqdm import tqdm
        from efficiency.nlp import NLP
        from efficiency.log import fwrite

        nlp = NLP()
        text = []

        pbar = tqdm(articles, desc='{} sents to {}'.format(0, file))
        for article in pbar:
            text += article.clean_paper(nlp)
            pbar.set_description('{} sents to {}'.format(len(text), file),
                                 refresh=True)

        text = list(set(text))
        import random
        random.shuffle(text)

        if file:
            fwrite('\n'.join(text), file)
        return text

    @staticmethod
    def postprocess_txt(native_txt, non_native_txt, eval_size=100, even=True):
        eval_native = []
        eval_non_native = []
        if even:
            import random

            min_len = min(len(native_txt), len(non_native_txt))
            if min_len < eval_size:
                eval_size = 0
            min_len -= eval_size
            random.shuffle(native_txt)
            random.shuffle(non_native_txt)
            if eval_size:
                eval_native = native_txt[-eval_size:]
                eval_non_native = non_native_txt[-eval_size:]

            native_txt = native_txt[:min_len]
            non_native_txt = non_native_txt[:min_len]
        return native_txt, non_native_txt, eval_native, eval_non_native

    @staticmethod
    def save_csv(txt_native, txt_non_native, file='articles_classified.csv'):
        import csv
        from efficiency.log import show_time

        with open(file, 'w') as f:
            writeout = [('native', line) for line in txt_native]
            writeout += [('non_native', line) for line in txt_non_native]

            writer = csv.writer(f)
            writer.writerows(writeout)

        show_time('[Info] Saved {}+{} sentences to {}'
                  .format(len(txt_native), len(txt_non_native), file))

    @staticmethod
    def run_classifier(file):
        import os
        from efficiency.log import show_time

        cmd = 'cp {} ../1909_prac_cls/data/pubmed/data.csv; ' \
              'cd ../1909_prac_cls/; ' \
              'python train.py -lower ' \
              '-data_dir data/pubmed -train_fname data.csv' \
              ''.format(file)
        import pdb;
        pdb.set_trace()
        os.system(cmd)
        show_time('[Info] Finished classification')


def lxml_get_1elem(lxml_obj, xpath):
    elem = lxml_obj.xpath(xpath)[0]
    return elem


def lxml_elem_list2text_list(lxml_elem_list):
    return [a.text for a in lxml_elem_list if a.text]


def lxml_elem2dict(lxml_elem):
    from lxml import etree
    import xmltodict

    string = etree.tostring(lxml_elem).decode('utf-8')
    dic = xmltodict.parse(string)
    return dic


class Article:
    TEXT_TAGS = [
        'p',
        'italic',
        'bold',
        'xref',
    ]
    USELESS_TAGS = [
        'supplementary-material',
        'inline-supplementary-material',
        'fig',
        'label',
        'caption',
        'ext-link',
        'title',
        'table-wrap',
    ]

    def __init__(self, lxml_data=None):
        self.lxml_data = lxml_data

    def lxml2json(self, article, use_all_secs=True):
        front = lxml_get_1elem(article, './/front')

        try:
            pmid = lxml_get_1elem(front, './/article-id[@pub-id-type="pmid"]').text
        except:
            pmid = 'None'
        # title = lxml_get_1elem(front, './/title-group//article-title').text
        # authors = front.xpath('.//contrib[@contrib-type="author"]')
        # authors = self._clean_authors(authors)
        affs = front.xpath('.//aff')
        affs = self._clean_affs(affs)
        # author_notes = front.xpath('.//author-notes')
        domains = front.xpath('.//author-notes//email') + \
                  front.xpath('.//contrib[@contrib-type="author"]//email')
        domains = lxml_elem_list2text_list(domains)
        domains = self._clean_domains(domains)
        abstracts = front.xpath('.//abstract//p')
        abstracts = lxml_elem_list2text_list(abstracts)

        body = lxml_get_1elem(article, './/body')
        body = self._clean_body(body)
        if use_all_secs:
            paper = [''.join(sec.itertext(*self.TEXT_TAGS)).strip()
                     for sec in body.xpath('.//sec//p')]
        else:
            paper = [''.join(sec.itertext(*self.TEXT_TAGS)).strip()
                     for sec in body.xpath('.//sec[@sec-type="intro"]//p')]
            paper += [''.join(sec.itertext(*self.TEXT_TAGS)).strip()
                      for sec in
                      body.xpath('.//sec[@sec-type="conclusion"]//p')]
        paper = abstracts + paper
        paper = [sec for sec in paper if len(sec.split()) > 10]

        data = {
            'domains': domains,
            'pmid': pmid,
            'paper': paper,
        }
        self.data = data

    def _clean_body(self, body):
        for tag in self.USELESS_TAGS:
            for elem in body.xpath('.//{}'.format(tag)):
                parent = elem.getparent()
                parent.remove(elem)
        return body

    def clean_paper(self, nlp):
        from efficiency.function import flatten_list
        text = [
            nlp.sent_tokenize(nlp.word_tokenize(s.replace('et al.', 'et al')))
            for s in self.data['paper']]
        text = [sent for sent in flatten_list(text) if len(sent.split()) > 8]
        self.data['paper'] = text
        return text

    def set_countries(self, country_checker):
        if 'countries' in self.data: return self.data['countries']
        try:
            coun = [
                country_checker.get_institution_country(d, enable_warning=False)
                for d in self.data['domains']]
        except:
            coun = []
        val_coun = set(coun) - {None}
        self.data['countries'] = val_coun
        return val_coun

    @staticmethod
    def _clean_domains(domains):
        domains = [d.split('@')[-1].strip('.') for d in domains]
        domains = list(set(domains) - {'', None})
        return domains

    @staticmethod
    def _clean_affs(affs):
        aff_dics = [lxml_elem2dict(a)['aff'] for a in affs]
        aff_dics = [{k: v for k, v in a.items() if not k.startswith('@')} for a
                    in aff_dics]
        return aff_dics

    @staticmethod
    def _clean_authors(authors):
        author_dics = []
        for a in authors:
            a = lxml_elem2dict(a)['contrib']
            if 'name' not in a:
                continue
            ref_text = []
            if 'xref' not in a:
                ref_text = [1]
            else:
                xrefs = a['xref'] if isinstance(a['xref'], list) else [
                    a['xref']]
                for xref in xrefs:
                    if xref['@ref-type'] == 'aff':
                        if '#text' in xref:
                            ref_text.append(xref['#text'])
                        elif 'sup' in xref:
                            ref_text.append(xref['sup'])

            author_dics.append({
                'name': a['name'],
                'xref': ref_text,
            })
        return author_dics


class CountryChecker(EmailCountryChecker):
    def __init__(self):
        super().__init__()

    @property
    def english_speaking_countries(self):
        '''
        by UK government standard
        https://www.sheffield.ac.uk/international/english-speaking-countries
        '''
        return {
            # 'Antigua and Barbuda',
            'Australia',
            # 'The Bahamas',
            # 'Barbados',
            # 'Belize',
            'Canada',
            # 'Dominica',
            # 'Grenada',
            # 'Guyana',
            'Ireland',
            # 'Jamaica',
            'New Zealand',
            # 'St Kitts and Nevis',
            # 'St Lucia',
            # 'St Vincent and the Grenadines',
            # 'Trinidad and Tobago',
            'United Kingdom',
            'United States',
        }


def download():
    import os
    path_chromdriver = '/usr/local/bin/chromedriver'
    if not os.path.isfile(path_chromdriver):
        from efficiency.function import shell
        url = 'https://chromedriver.storage.googleapis.com/78.0.3904.11/chromedriver_linux64.zip'
        cmd = 'curl -O {} \n' \
              'unzip chromedriver_linux64.zip \n ' \
              'rm chromedriver_linux64.zip'.format(url)
        shell(cmd)
    import pdb;
    pdb.set_trace()

    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options

    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("start-maximized")
    options.add_argument("disable-infobars")
    options.add_argument("--disable-extensions")
    driver = webdriver.Chrome(chrome_options=options,
                              executable_path=path_chromdriver)
    driver.get('http://google.com/')
    import pdb;
    pdb.set_trace()

    from selenium import webdriver
    driver = webdriver.Chrome()
    driver.get('https://www.ncbi.nlm.nih.gov/pmc/?term=paper')
    driver.find_element_by_id('sendto').find_element_by_xpath('.//a').click()
    driver.find_element_by_id('dest_File').click()
    driver.find_element_by_xpath(
        './/button[@name="EntrezSystem2.PEntrez.PMC.Pmc_ResultsPanel.Pmc_DisplayBar.SendToSubmit"@sid="1"@class="button_apply file ncbipopper-close-button"@type="submit"@cmd="File"]')
    import pdb;
    pdb.set_trace()
    driver.quit()


def main():
    import os

    # download()

    folder = 'data/'
    fnames = [
        # 'pmc_result.xml',
        # 'pmc_result_one_good.xml',
        'pmc_result_china_journal2.xml',
        'pmc_result_china_PMC_live_date2.xml',
    ]
    files = [os.path.join(folder, fname) for fname in fnames]

    dataset = Dataset(files, use_all_secs=False, save_to=3)


if __name__ == '__main__':
    main()
