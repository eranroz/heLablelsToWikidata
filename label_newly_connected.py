"""
Update wikidata labels based on recently articles connected to wikidata
"""
import datetime
import pywikibot
from pywikibot import pagegenerators

local_wiki = pywikibot.Site()
wikidata = local_wiki.data_repository()
wikidata.login()
#st = local_wiki.getcurrenttime()
st = local_wiki.server_time()
wd_changes = wikidata.recentchanges(changetype='edit', namespaces=[0], bot=False,
                                    start=st, end=st-datetime.timedelta(days=1))
new_local_sitelinks = (pywikibot.ItemPage(wikidata, e['title']) for e in wd_changes if e['comment'].startswith('/* wbsetsitelink-add:1|hewiki'))
# preload
new_local_sitelinks = pagegenerators.PreloadingEntityGenerator(new_local_sitelinks)
for data_item in new_local_sitelinks:
    if local_wiki.lang in data_item.labels or local_wiki.dbName() not in data_item.sitelinks:
        continue
    local_page = pywikibot.Page(local_wiki, data_item.getSitelink(local_wiki))
    if local_page.namespace() not in [0, 14]:
        continue
    he_title = local_page.title()
    print('Setting label %s: %s'% (data_item.title(), he_title))
    try:
        wikidata._simple_request(**({
            'action': 'wbsetlabel',
            'id': data_item.title(),
            'value': he_title,
            'language': local_wiki.lang,
            'token': wikidata.tokens['csrf']
        })).submit()
    except pywikibot.exceptions.APIError as e:
        continue
