import flask as fk
import requests
import re
from lxml import html
from bs4 import BeautifulSoup
import pandas as pd
import nltk
import copy
from nltk.tokenize import word_tokenize 
from flask import jsonify, redirect
import time

app = fk.Flask(__name__)

invertedIndex = {}
tokenDocuments = {}
urlArray = []
titles = []


def generateingInvertedIndex():
    with open("urls.txt", "r") as f2:
        stocks = f2.read().splitlines()
    for stock in stocks:
        urlArray.append(stock)
    for index, url in enumerate(urlArray):
        r = requests.get(url)
        c = r.content
        soup = BeautifulSoup(c, 'html.parser')
        body = soup.find('body')
        title = soup.find("title").text
        tagsP = body.find_all('p')
        texts = ""
        titles.append(title)
        for p in tagsP:
            if p.string != None:
                texts += p.string + " "
        loweredText = texts.lower()
        tokens = nltk.word_tokenize(loweredText)
        tokens = [r.encode('utf-8') for r in tokens]
        tokenDocuments[str(index)] = tokens

        for token in tokens:
            if(not(token in invertedIndex)):
                invertedIndex[token] = [index]
            else:
                if(not(index in invertedIndex[token])):
                    invertedIndex[token].append(index)  

generateingInvertedIndex()

for ky in invertedIndex:
    print(ky, invertedIndex[ky])

def positionalIntersection(p1, p2, k, answer):
    docIDp1 = sorted(p1.keys())
    docIDp2 = sorted(p2.keys())

    while (len(docIDp1) > 0 and len(docIDp2) > 0) :
        if(docIDp1[0] == docIDp2[0]):
            i = []
            pp1 = copy.copy(p1[docIDp1[0]])
            pp2 = copy.copy(p2[docIDp2[0]])
            while(len(pp1) > 0):
                while(len(pp2) > 0):
                    if(pp2[0] - pp1[0] == k):
                        i.append(pp2[0])
                    elif(pp2[0] > pp1[0]):
                        break
                    pp2.pop(0)
                while(len(i) > 0 and abs(i[0] - pp1[0]) > k):
                    i.pop(0)
                for element in i:
                    if(not(docIDp1[0] in answer)):
                        answer[docIDp1[0]] = set([pp1[0], element])
                    else:
                        answer[docIDp1[0]].add(pp1[0])
                        answer[docIDp1[0]].add(element)
                pp1.pop(0)
            docIDp1.pop(0)
            docIDp2.pop(0)
        elif( int(docIDp1[0]) < int(docIDp2[0]) ):
            docIDp1.pop(0)
        else:
            docIDp2.pop(0)


@app.route('/')    
def init():
    return fk.render_template('index.html')

@app.route('/results', methods=['POST'])
def search():
    start = time.time()
    answer = {}
    inputedText = fk.request.form['text']
    lowerCaseInputed = inputedText.lower()
    tokens = nltk.word_tokenize(lowerCaseInputed)
    positionalIndex = {}
    for token in tokens:
        if not(token in positionalIndex):
            positionalIndex[token] = {}
            docs = []
            if token in invertedIndex:
                docs = invertedIndex[token]
            for docID in docs:
                positionalIndex[token][str(docID)] = []
                for index, tk in enumerate(tokenDocuments[str(docID)]):
                    if tk == token:
                        positionalIndex[token][str(docID)].append(index)
    if (len(tokens) >= 2):
        for i in range(1, len(tokens)):
            p1 = {}
            p2 = {}
            if(tokens[i-1] in positionalIndex):
                p1 = positionalIndex[tokens[i-1]]
            if(tokens[i] in positionalIndex):
                p2 = positionalIndex[tokens[i]]
            positionalIntersection(p1, p2, 1, answer)
    elif (len(tokens) == 1):
        if(tokens[0] in positionalIndex):
            answer = positionalIndex[tokens[0]]
    for key in answer:
        answer[key] = sorted(answer[key])
    end = time.time()
    print(answer)

    return fk.render_template('result.html', answer = answer, urlArray = urlArray, titles=titles, numberOfResults=len(answer.keys()), time=(end-start), inputed=inputedText)



