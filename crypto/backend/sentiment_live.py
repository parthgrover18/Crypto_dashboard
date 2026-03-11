import mwclient
import time
from transformers import pipeline
from statistics import mean 
import pandas as pd
from datetime import datetime


# wiki
site=mwclient.Site('en.Wikipedia.org')
page=site.pages['Bitcoin']
revs=list(page.revisions())

revs=sorted(revs, key=lambda rev:rev['timestamp'])

# revs = [
#     [
#         ('revid', 275832581),
#         ('parentid', 0),
#         ('user', 'Pratyeka'),
#         ('timestamp', time.struct_time((2009, 3, 8, 16, 41, 7, 6, 67, -1))), 
#         ('comment', 'creation (stub)')
#     ],
#     [
#         ('revid', 275832690),
#         ('parentid', 275832581),
#         ('user', 'Pratyeka'),
#         ('timestamp', time.struct_time((2009, 3, 8, 16, 41, 44, 6, 67, -1))), 
#         ('comment', '')
#     ],
#     [
#         ('revid', 275849499),
#         ('parentid', 275832690),
#         ('user', 'PamD'),
#         ('timestamp', time.struct_time((2009, 3, 9, 18, 12, 46, 6, 67, -1))),
#         ('comment', 'Stub-sorting. [[Wikipedia:WikiProject Stub sorting|You can help!]]')
#     ]
# ]

# senti analysis
sentiment_pipeline = pipeline(
    'sentiment-analysis', 
    model='distilbert-base-uncased-finetuned-sst-2-english'
)

def find_sentiment(text):
    
    # sent gives this: [{'label': 'POSITIVE', 'score': 0.9998656511306763}]
    
    sent=sentiment_pipeline([text])[0]
    score=sent['score']
    if sent['label']=='NEGATIVE':
        score*=-1
    return score


edits={}


# calculating sentiment value of each list and storing them in edits
for rev in revs:
    date=time.strftime("%Y-%m-%d", rev['timestamp']) # rev['timestamp']     rev[3][1]

    if date not in edits:
        edits[date]=dict(sentiments=list(), edit_count=0)
    
    edits[date]['edit_count']+=1

    rev_dict = dict(rev)
    

    if 'comment' not in rev_dict.keys():
        rev_dict['comment']=''
    
    comment = rev_dict['comment']

    # comment=next(value for key, value in rev if key == 'comment') # rev['comment']       rev[4][1]
    edits[date]['sentiments'].append(find_sentiment(comment))


# calculating mean of multiple sentiment values and finding a negative sentiment percentage out of 1
for key in edits:
    if len(edits[key]['sentiments'])>0:
        edits[key]['sentiment']=mean(edits[key]['sentiments'])
        edits[key]['neg_sentiment']=len([s for s in edits[key]['sentiments'] if s<0]) / len(edits[key]['sentiments'])
    
    else:
        edits[key]['sentiment']=0
        edits[key]['neg_sentiment']=0
    
    del edits[key]['sentiments']

print('\n')
print('\n')
print('edits:')
print(edits)

edits_df=pd.DataFrame.from_dict(edits, orient='index')
edits_df.index=pd.to_datetime(edits_df.index)

dates=pd.date_range(start='2009-03-08', end=datetime.today())
edits_df=edits_df.reindex(dates, fill_value=0)

rolling_edits=edits_df.rolling(30).mean()
rolling_edits=rolling_edits.dropna()

print('\n')
print('\n')
print('edits_df:')
print(edits_df)

rolling_edits.to_csv('backend/Wikipedia_edits.csv')



#  tweets, news articles,


# consumer_key = 'Y6fly7z9uIcB0S8ttJfRCwfim'
# consumer_secret = 'D5HAwAseXvJkOwvF2N3k8ur5pcneuBp48dybEfqmEPjFyqinFM'
# access_token = '1227131736934367232-DSlCC9tX6QyRqaANmfpy2bX6OzLkZz'
# access_token_secret = 'KGu5dxi7TBNv4Eef2OXGr2iesRtb54KxAjslDTD4Zahd2'
# bearer_token='AAAAAAAAAAAAAAAAAAAAAMBkzwEAAAAA5sjy2btfAQ%2B1kmhOKM89PvykB4g%3DONpZaZ63NJDwNPvXXRwlnVUTbYPwIuR1xX0RLrLAphsimC8FTb'
