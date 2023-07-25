import re

from matplotlib import pyplot as plt

text_file = open("total_stopword.txt", "r")
total_stopword = text_file.read().split('\n')
total_stopword=set(total_stopword[0:(len(total_stopword)-1)])

def remove_stopwords(sentence, custom_stopword=[]):
    agg_stopwords=list(set(custom_stopword+list(total_stopword)))
    sentence_list=sentence.split(" ")
    new_sentence=[]
    for word in sentence_list:
        if word.lower() not in agg_stopwords and len(word)>2:
            new_sentence.append(word)
    return " ".join(new_sentence)

def count_emoji(sentence):
    return len(re.findall('[\U0001f600-\U0001f650]', sentence))


def count_unique_users(np_user_list):
    return len(set(list(np_user_list)))

def reply_count(x):
    try:
        count=len(x)
        count=1
    except:
        count=0
    return count


def mention_list(json_mention):
    """
    :param json file or na:
    :return:
    """

    try:
        return [x['id'] for x in json_mention]
    except:
        return []


def flatten_lower_ner_list(nested_list):
    ner_list=[x for x in nested_list if not x==[]]
    ner_list=[x for sublist in ner_list for x in sublist]
    return ner_list

def clean_user_list(list_of_user):
    """
    input: list_of_User is a result of pd groupby, the inpt is a pd series
    """
    list_of_user=list(list_of_user)
    list_of_user=flatten_lower_ner_list(list_of_user)
    return list(set(list_of_user))
