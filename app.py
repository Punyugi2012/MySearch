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
positionalIndex = {}
urls = []
titles = []
tokenDocuments = []


def loadURLsFromFile():
    with open("urls.txt", "r") as f2:
        stocks = f2.read().splitlines()
    for stock in stocks:
        urls.append(stock)

def setupTokenDocuments():
    global tokenDocuments
    for index, url in enumerate(urls):
        r = requests.get(url)
        c = r.content
        soup = BeautifulSoup(c, 'html.parser')
        body = soup.find('body')
        title = soup.find("title").text
        titles.append(title)
        pElements = body.find_all('p')
        words = ""
        tokens = []
        for p in pElements:
            if p.string != None:
                words += p.string + " "
        words = nltk.word_tokenize(words)
        tokens = [word.lower() for word in words if word.isalpha()]
        tokens = [r.encode('utf-8') for r in tokens]
        tokenDocuments.append(tokens)

def generateInvertedIndex():
    for urlIndex, tokens in enumerate(tokenDocuments):
        for token in tokens:
            if(not(token in invertedIndex)):
                invertedIndex[token] = [urlIndex]
            else:
                if(not(urlIndex in invertedIndex[token])):
                    invertedIndex[token].append(urlIndex)  

def generatePositionalIndex():
    for token in invertedIndex:
        if not(token in positionalIndex):
            positionalIndex[token] = {}
            for docID in invertedIndex[token]:
                positionalIndex[token][str(docID)] = []
                for index, word in enumerate(tokenDocuments[docID]):
                    if word == token:
                        positionalIndex[token][str(docID)].append(index)

def getPriority(token):
  if (token == 'AND' or token == 'OR'):
    return 1
  if (token == 'NOT'):
    return 2
  return 3

def getComplement(list):
  result = set([])
  for key in invertedIndex.keys():
    subtracted = set(invertedIndex[key]) - set(list)
    result = result.union(subtracted)
  return result


def unionMultiple(list):
  result = set(list[0])
  for i in range(1, len(list)):
    result = result.union(set(list[i]))
  return result

def intersectingMultiple(list):
  if len(list) == 0:
    return 0
  result = set(list[0])
  for i in range(1, len(list)):
    result = result.intersection(set(list[i]))
  return result

def booleanSearch(tokens):
  postFix = []
  tmpStack = []
  for token in tokens:
    if (token != 'AND' and token != 'OR' and token != 'NOT' and token != '(' and token != ')'):
      postFix.append(token)
    else:
      if len(tmpStack) == 0:
        tmpStack.append(token)
      else:
        if (token == '('):
          tmpStack.append(token)
        elif (token == ')'):
          while ( not(len(tmpStack) == 0) and tmpStack[-1] != '(' ):
            postFix.append(tmpStack.pop())
          tmpStack.pop()
        else:
          if ( getPriority(token) >= getPriority(tmpStack[-1]) ):
            while ( not(len(tmpStack) == 0) and getPriority(token) >= getPriority(tmpStack[-1]) ):
              postFix.append(tmpStack.pop())
            tmpStack.append(token)
          else:
            tmpStack.append(token)
  if (len(tmpStack) > 0):
    postFix.append(tmpStack.pop())
  stackOperand = []
  for token in postFix:
    if (token != 'AND' and token != 'OR' and token != 'NOT' and token != '(' and token != ')'):
      if (token in invertedIndex):
        stackOperand.append(invertedIndex[token])
      else:
        stackOperand.append([])
    else:
      if (token == 'NOT'):
        first = stackOperand.pop()
        result = getComplement(first)
        stackOperand.append(result)
      else:
        if len(stackOperand) >= 2:
          first = stackOperand.pop()
          second = stackOperand.pop()
          if (token == 'AND'):
            result = intersectingMultiple([first, second])
            stackOperand.append(result)
          elif (token == 'OR'):
            result = unionMultiple([first, second])
            stackOperand.append(result)

  return stackOperand


loadURLsFromFile()
setupTokenDocuments()
generateInvertedIndex()
generatePositionalIndex()

print("InvertedIndex")
for key in invertedIndex:
    print(key, invertedIndex[key])
print("----------")

print("PositionalIndex")
for key in positionalIndex:
    print(key, positionalIndex[key])
print("----------")

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
                    if(abs(pp1[0] - pp2[0]) <= k):
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
    inputedWords = fk.request.form['text']
    if len(inputedWords) > 0:
        if inputedWords.startswith('"') and inputedWords.endswith('"'):
            start = time.time()
            answer = {}
            inputedWords = inputedWords.replace('"', '')
            inputedWords = nltk.word_tokenize(inputedWords)
            inputedTokens = [word.lower() for word in inputedWords if word.isalpha()]
            inputedTokens = [r.encode('utf-8') for r in inputedTokens]
            if (len(inputedTokens) >= 2):
                for i in range(1, len(inputedTokens)):
                    p1 = {}
                    p2 = {}
                    if(inputedTokens[i-1] in positionalIndex):
                        p1 = positionalIndex[inputedTokens[i-1]]
                    if(inputedTokens[i] in positionalIndex):
                        p2 = positionalIndex[inputedTokens[i]]
                    positionalIntersection(p1, p2, 1, answer)
            elif (len(inputedTokens) == 1):
                if(inputedTokens[0] in positionalIndex):
                    answer = positionalIndex[inputedTokens[0]]
            for key in answer:
                answer[key] = sorted(answer[key])
            tmpAnswer = answer.copy()
            for a in tmpAnswer:
                if(len(tmpAnswer[a])>1):
                    count = 1
                    for i in range(1, len(tmpAnswer[a])):
                        if (tmpAnswer[a][i] - tmpAnswer[a][i-1] != 1):
                            break
                        else:
                            count += 1
                    if count < len(inputedTokens):
                        del answer[a]
            docIdAnswer = []
            for answer in answer:
                docIdAnswer.append(int(answer))
            docIdAnswer = sorted(docIdAnswer)
            print(docIdAnswer)
            end = time.time()
            return fk.render_template('result.html', inputed = fk.request.form['text'], urls = urls, titles = titles, time = (end-start), algorithm = 'ProximitySearch', docIdAnswer = docIdAnswer, nbsAnswer = len(docIdAnswer))
        else:
            start = time.time()
            inputedWords = nltk.word_tokenize(inputedWords)
            inputedWords = [r.encode('utf-8') for r in inputedWords]
            for (index, word) in enumerate(inputedWords):
                if word != "AND" and word != "OR" and word != "NOT":
                    inputedWords[index] = word.lower()
            results = booleanSearch(inputedWords)
            docIdAnswer = []
            if len(results) > 0:
                for docId in results[0]:
                    docIdAnswer.append(docId)
            docIdAnswer = sorted(docIdAnswer)
            print(docIdAnswer)
            end = time.time()
            return fk.render_template('result.html', inputed = fk.request.form['text'], urls = urls, titles = titles, time = (end-start), algorithm = 'BooleanSearch', docIdAnswer = docIdAnswer, nbsAnswer = len(docIdAnswer))
    else:
        return 'Input Invalid'

