'''
@author: Zhijing Jin
adapt this file if you need to download and clean the xml file.
'''

import os
def check_env():
    try:
        import torchtext
        import efficiency
    except ImportError:
        cmd = 'pip install torchtext efficiency'
        os.system(cmd)

def download_from_url(
        url='https://www.dropbox.com/sh/a82floo76wzcf7w/AADhezfn4afQHT1POqTVu4Bva?dl=1'
):
    from torchtext.utils import download_from_url

    download_from_url(url, root='.')

def fix_corrupted_file(file):
    from efficiency.function import shell

    cmd ='grep -nriF "</article>" {file} | tail -n1 |cut -d ":" -f 1 '\
        .format(file=file)
    outp, err = shell(cmd)
    n_line = outp.strip()
    cmd = 'head -{n_line} {file} > temp; ' \
          'tail -n2 temp; ' \
          'echo "</pmc-articleset>" >> temp; ' \
          'mv temp {file}'.format(n_line=n_line, file=file)
    os.system(cmd)

def main():
    download_from_url()
    # xml_file = 'pmc_result.xml'
    # fix_corrupted_file(xml_file)
if __name__ == '__main__':
    main()