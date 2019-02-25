from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize 
import nltk
import copy

# nltk.download('punkt')
  
# example_sent = "to be not or to be"
  
# stop_words = set(stopwords.words('english')) 
  
# word_tokens = word_tokenize(example_sent) 

# filtered_sentence = [w for w in word_tokens if not w in stop_words] 
  
# filtered_sentence = [] 
  
# for w in word_tokens: 
#     if w not in stop_words: 
#         filtered_sentence.append(w) 
  
# print(word_tokens) 
# print(filtered_sentence) 

inputed = "to be"

positionalIndex = {
    "to": {
        "3": [12]
    },
    "be": {
        "3": [11]
    }
    # "to": {
    #     "1": [7, 18, 33, 72, 86, 231],
    #     "2": [1, 17, 74, 222, 255],
    #     "4": [8, 16, 190, 429, 433],
    #     "5": [363, 367],
    #     "7": [13, 23, 191]
    # },
    # "be": {
    #     "1": [17, 25],
    #     "4": [17, 191, 291, 430, 434],
    #     "5": [14, 19, 101]
    # }
}

answer = {}

def positionalIntersection(p1, p2, k):

    docIDp1 = sorted(p1.keys())
    docIDp2 = sorted(p2.keys())

    while (len(docIDp1) > 0 and len(docIDp2) > 0) :
        if(docIDp1[0] == docIDp2[0]):
            i = []
            pp1 = copy.copy(p1[docIDp1[0]])
            pp2 = copy.copy(p2[docIDp2[0]])
            while(len(pp1) > 0):
                while(len(pp2) > 0):
                    if(abs(pp2[0] - pp1[0]) == k):
                        i.append(pp2[0])
                    elif(pp2[0] > pp1[0]):
                        break
                    pp2.pop(0)
                while(len(i) > 0 and abs(i[0] - pp1[0]) > k):
                    i.pop(0)
                for element in i:
                    if(not(docIDp1[0] in answer)):
                        answer[docIDp1[0]] = [pp1[0], element]
                    else:
                        answer[docIDp1[0]].append(pp1[0])
                        answer[docIDp1[0]].append(element)
                pp1.pop(0)
            docIDp1.pop(0)
            docIDp2.pop(0)
        elif( int(docIDp1[0]) < int(docIDp2[0]) ):
            docIDp1.pop(0)
        else:
            docIDp2.pop(0)
                
tokens = nltk.word_tokenize(inputed)
if (len(tokens) >= 2):
    for i in range(1, len(tokens)):
        p1 = {}
        p2 = {}
        if(tokens[i-1] in positionalIndex):
            p1 = positionalIndex[tokens[i-1]]
        if(tokens[i] in positionalIndex):
            p2 = positionalIndex[tokens[i]]
        positionalIntersection(p1, p2, 1)
elif (len(tokens) == 1):
    if(tokens[0] in positionalIndex):
        answer = positionalIndex[tokens[0]]

positionalIntersection(positionalIndex["to"], positionalIndex["be"], 1)

print(answer)
