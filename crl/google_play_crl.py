import pandas as pd
from bs4 import BeautifulSoup
import re
from pprint import pprint
import seaborn as sns
import matplotlib.pyplot as plt
import json
import warnings
import numpy as np
from konlpy.tag import Twitter
from sklearn.feature_extraction.text import CountVectorizer
from PIL import Image
from wordcloud import WordCloud, STOPWORDS


df = pd.read_json("google_re.json")

p = re.compile(r'\d+')


def parser(body):
    bs = BeautifulSoup(body, 'html.parser')
    user_name = bs.find('span', class_='X43Kjb').text
    date = bs.find('span', class_='p2TkOb').text
    rating = bs.find('div', {'role': 'img'})['aria-label']
    rating = p.findall(rating)[-1]
    review_text = bs.find('span', {'jsname': 'bN97Pc'}).text
    return user_name, date, rating, review_text

def get_word_low_rating(sentence):
    nouns = low_tagger.nouns(sentence)
    return [noun for noun in nouns if len(noun) > 1]

def get_word_high_rating(sentence):
    nouns = high_tagger.nouns(sentence)
    return [noun for noun in nouns if len(noun) > 1]


df['user_name'], df['date'], df['rating'], df['review_text'] = zip(*df['body'].map(parser))
del df["body"]

df['date'] = pd.to_datetime(df['date'], format='%Y년 %m월 %d일')

df = df.sort_values(by='date', ascending=False).reindex()

sns.factorplot('rating',kind='count',data=df)

# XlsxWriter 엔진으로 Pandas writer 객체 만들기
writer = pd.ExcelWriter('pandas_xlsxWriter.xlsx', engine='xlsxwriter')

# DataFrame을 xlsx에 쓰기
df.to_excel(writer, sheet_name='Sheet1')

# Pandas writer 객체 닫기
writer.close()


high_rate_review = df[df['rating'] == '5']['review_text']
low_rate_review = df[df['rating'] <= '2']['review_text']

high_rate_review = high_rate_review.apply(lambda x:re.sub('[^가-힣\s\d]',"",x))
low_rate_review = low_rate_review.apply(lambda x:re.sub('[^가-힣\s\d]',"",x))

low_tagger = Twitter()
high_tagger = Twitter()

low_countvector = CountVectorizer(tokenizer=get_word_low_rating, max_features=300)
low_tdf = low_countvector.fit_transform(low_rate_review)
low_words = low_countvector.get_feature_names()

count_mat = low_tdf.sum(axis=0)
count = np.squeeze(np.asarray(count_mat))
low_rating_word_count = list(zip(low_words, count))
low_rating_word_count = sorted(low_rating_word_count, key=lambda t:t[1], reverse=True)

high_countvector = CountVectorizer(tokenizer=get_word_high_rating, max_features=300)
high_tdf = high_countvector.fit_transform(high_rate_review)
high_words = high_countvector.get_feature_names()

count_mat = high_tdf.sum(axis=0)
count = np.squeeze(np.asarray(count_mat))
high_rating_word_count = list(zip(high_words, count))
high_rating_word_count = sorted(high_rating_word_count, key=lambda t:t[1], reverse=True)

low_rating_document = low_rate_review.values
high_rating_document = high_rate_review.values

font_path = '/Users/ghun/Library/Fonts/BMJUA_otf.otf'
wc = WordCloud(width = 1000, height = 800, background_color="white", font_path=font_path).generate(np.array2string(high_rating_document))
plt.figure(figsize=(6, 5), dpi=120)
plt.imshow(wc, interpolation='bilinear')
plt.axis("off")
plt.show()

# pprint(df)
# print(len(df))
# pprint(sns)
#
# print("최소 :", min(df['date'].value_counts().index))
# print("최대 :", max(df['date'].value_counts().index))
# print(df['rating'].value_counts())