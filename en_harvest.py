"""
This is a simple script to extract English terms and related Hebrew terms
(based on Template:אנ in hewiki), and enrich Wikidata accordingly.

CAUTION: It is based on heuristic. It is YOUR responsibility to make sure the output is correct.
"""
import re
import pywikibot
import pickle
from pywikibot.tools import itergroup

ensite = pywikibot.Site('en')
data_repo = ensite.data_repository()
data_repo.login()
enwiki_templates = [pywikibot.Page(pywikibot.Site(), 'תבנית:אנ'), pywikibot.Page(pywikibot.Site(), 'תבנית:אנג')]
valid_namespace = [0, 10, 14, 100]
transcluding_pages = (p for entemp in enwiki_templates for p in entemp.getReferences(follow_redirects=True,
                                                                                     withTemplateInclusion=True,
                                                   onlyTemplateInclusion=True, content=True,
                                                                                     namespaces=valid_namespace))

entemplate_rgx = re.compile('\[\[([^]\[|]+?)\]\] *\(?\{\{אנג?\|(?:1=)? *([^|]+?)\}\}')
try:
    with open('existing_labels.pkl', 'rb') as existing_backup:
        existing_labels = pickle.load(existing_backup)
except FileNotFoundError:
    existing_labels = set()
english_to_hebrew_labels = ((english_label.replace('_', ' ').strip(), hebrew_label) for page in transcluding_pages
                            for hebrew_label, english_label in entemplate_rgx.findall(page.get())
                            if english_label not in existing_labels)

i = 0
for sublist in itergroup(english_to_hebrew_labels, 50):
    print('Query labels: %i' % i)
    i += 50
    eng_heb_dict = dict(sublist)
    for en in eng_heb_dict.keys():
        existing_labels.add(en)
    req = {'titles': '|'.join(eng_heb_dict.keys()),
           'sites': 'enwiki',
           'action': 'wbgetentities',
           'props': 'labels|sitelinks',
           'sitefilter': 'enwiki',
           'languages': 'he|en'}

    wbrequest = data_repo._simple_request(**req)
    wbdata = wbrequest.submit()
    entities_require_label = [item for item in wbdata['entities'].values() if
                              'labels' in item and 'he' not in item['labels']]

    for item in entities_require_label:
        try:
            entity_label = eng_heb_dict[item['sitelinks']['enwiki']['title']]
        except:
            print('Couldnt find %s' % item['sitelinks']['enwiki']['title'])
            continue
        print('%s => %s' % (item['sitelinks']['enwiki']['title'], entity_label))
        data_repo._simple_request(**({
            'action': 'wbsetlabel',
            'id': item['id'],
            'value': entity_label,
            'language': 'he',
            'token': data_repo.token(None, 'csrf')
        })).submit()
pickle.dump(existing_labels, open('existing_labels.pkl', 'wb'))