from fuzzywuzzy import fuzz
from fuzzywuzzy import process
from itertools import groupby
from word2number import w2n
import nltk
import code
import usaddress
import re

def underscore(name):
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

def isfloat(x):
    try:
        a = float(x)
    except ValueError:
        return False
    else:
        return True

def isprice(x):
    #\$*\d+(\.\d+?)([MmkK])*|\d+(\.\d+)?\$
    return re.findall(r'(\d+(\.\d+)?)([MmkK])?', x)

def price_to_num(x):
    multipliers = {'k': 10**3, 'K': 10**3, 'm': 10**6, 'M': 10**6}

    if x[-1] in multipliers:
        return float(x[0]) * multipliers[x[-1]]
    else:
        return float(x[0])


# Messages analizers =======================================================================

def group_by_category(statements, groups):
    for s in statements:
        groups[s[0]].append(s)

    return groups

def analyze_message(msg, sets, scorer):
    result = []
    for key, set in sets.iteritems():
        best_score = process.extractOne(msg, set, scorer=scorer)[1]
        result.append(tuple([key, best_score]))

    return result

def choose_top_category(scores, msg):
    top_set = sorted(scores, key=lambda (k): (k[1]), reverse=True)[0]
    top_set += (msg,)

    return top_set

def analyze_messages(word_lists, sets, scorer):
    result = []
    for word_list in word_lists:
        msg = u"{}".format(",".join(word_list))
        scores = analyze_message(msg, sets, scorer)
        analyzed_messages = choose_top_category(scores, msg)
        result.append(analyzed_messages)

    return result

# message parsers =======================================================================

def default_response():
    return 'Try some other message, please!'

def greetings_response(statement):
    return ['Good day!', True]

def actions_response(statement):
    action_statements = analyze_message(statement, actions_parse, fuzz.token_set_ratio)
    action_statements.sort(key=lambda tup: tup[1], reverse=True) # top tuple by scores [('buy', 100), ('rent', 33), ('sell', 0)]

    return [action_statements[0][0], True]

def beds_response(statement):
    return parse_number(statement)

def baths_response(statement):
    return parse_number(statement)

def address_response(statement):
    #parse state, streed, home number
    return parse_address(statement)

def hasNumbers(inputString):
    return any(char.isdigit() for char in inputString)

def parse_number(statement):
    result = None
    has_number = False
    number_index = 0
    tokens = nltk.word_tokenize(statement)
    tagged = nltk.pos_tag(tokens)

    for i, tag in enumerate(tagged):
        if tag[1] == 'CD':
            has_number = True
            number_index = i
            result = tag[0].replace(",", ".") # 3.5 of three
            if not isfloat(result):
                result = w2n.word_to_num(result)

    return [result, has_number, number_index, len(tokens)]

# def parse_price(statement):
#     matches = isprice(statement[2].replace(",", "."))

#     result = None
#     min_price = 0
#     max_price = 0

#     if len(matches) == 1:
#         max_price = price_to_num(matches[0][0] + matches[0][2])
#     elif len(matches) == 2:
#         min_price = price_to_num(matches[0][0] + matches[0][2])
#         max_price = price_to_num(matches[1][0] + matches[1][2])

#     return { 'min_price': min_price, 'max_price': max_price }

        # prices_obj = parse_price(statements[0])
        # if prices_obj['min_price'] > 0:
        #     result_push(result, 'min_price', prices_obj['min_price'], agent)
        # if prices_obj['max_price'] > 0:
        #     result_push(result, 'max_price', prices_obj['max_price'], agent)

def parse_price(statements):
    all_mathces = []
    for word_list in statements:
        msg = u"{}".format(",".join(word_list))
        matches = isprice(msg)
        all_mathces.append(matches)

    flatten = [x for sublist in all_mathces for x in sublist]
    uniq_matches = list(set(flatten))
    prices = map(lambda x: price_to_num(x), uniq_matches)
    sorted_matches = sorted(prices, key=float)
    return sorted_matches

def parse_address(statement):
    address = usaddress.tag(statement)
    return dict(address[0])


# =======================================================================


# text wrappers =======================================================================

def greetings_wrap(message):
    return "Hi I'm Agent Smith. I can help you find a home."

def actions_wrap(message):
    return 'I will help you ' + message + ' a home.'

def beds_wrap(message):
    return 'You want home with '+ message + ' bed(s).'

def baths_wrap(message):
    return 'You want home with '+ message + ' bath(s).'

def min_price_wrap(message):
    return 'Min price: ' + message

def max_price_wrap(message):
    return 'Max price: ' + message

def address_wrap(message):
    #parse state, streed, home number
    return 'I now your future address.'

# =======================================================================

# Questions generations ========================================================

def actions_question():
    return 'Do you want buy, sell or rent a home?'

def general_question():
    return "Could you tell me a little about the home you're looking for? Like the number of beds/baths, location, price or any specific features you're looking for."

def beds_question():
    return 'How many beds do you want?'

def baths_question():
    return 'How many baths do you want?'

def price_question():
    return "What budget are you looking for a home in?"#'How much money do you have for home?'

def address_question():
    return 'Please tell me address do you want?'

def final_question():
    return "Here are some homes I think you'll like!"

# ============================================================================



# bot API functions =======================================================================

def questions_category(category):
    switcher = {
        'actions': 'actions_question',
        'general': 'general_question',
        'beds': 'beds_question',
        'baths': 'baths_question',
        'max_price': 'price_question',
        'address': 'address_question',
        None: 'final_question'
    }
    func = switcher.get(category)
    return globals()[func]()


def perform_category(category, statement):
    switcher = {
        'greetings': 'greetings_response',
        'actions': 'actions_response',
        'beds': 'beds_response',
        'baths': 'baths_response',
        'address': 'address_response'
    }

    func = switcher.get(category)
    return globals()[func](statement)

def wrap_category(category, sentence):
    switcher = {
        'greetings': 'greetings_wrap',
        'actions': 'actions_wrap',
        'beds': 'beds_wrap',
        'baths': 'baths_wrap',
        'min_price': 'min_price_wrap',
        'max_price': 'max_price_wrap',
        'address': 'address_wrap'
    }
    func = switcher.get(category)
    return globals()[func](str(sentence))

def answer_category(category, statements):
    results = []
    for statement in statements:
        if statement[1] > 80:
            response = perform_category(category, statement[2]) # array ['int', True]
            
            if response[1] == True:
                results.append(response[0])  # only parsed integers
                break

    return results  
  


greetings = ["Hello", "Hi", "Goog day", "Good morning", 'Greetings', 'Hey', 'Whats up',
'good morning', 'good day', 'good evening', 'goog afternoon']

actions = ["Sell", "Buy", "Rent", "Looking for", 'find me', 'could you find',
'could you find me a home', 'I am looking for', "I'm looking for a home"] #"I want buy", "I want sell", 
actions_parse = {'buy': ['buy', "Looking for", 'find me', 'could you find',
'could you find me a home', 'I am looking for', "I'm looking for a home"], 'sell':['sell'], 'rent':['rent']} # [('buy', 100), ('rent', 33), ('sell', 0)]

beds = ["bed", "beds", "bedroom", 'bedrooms']
baths = ["bath", "baths", "bathrooms", "bathroom"]
min_price = [] #["under", "min price", "max price", "price", "budget", 'between']
max_price = []
address = ["address", "street", "state", "placement"]

sets = {'greetings' : greetings, 'actions' : actions,
		'beds' : beds, 'baths' : baths}

answer_message = "Here are some homes I think you'll like!"
bundget_question = "What budget are you looking for a home in?"# "What's your budget for this home?"
#"I'm sorry, we dont have any data on that area! Try another."
#We couldn't find any results with your preferences.
#Your search preferences have been cleared. Please enter the following to get new results: location, price, beds, baths, interests

# TODO
# double questions - beds and baths ?
# min price, max price, between price
# parse address CITY, STATE - Austin, TX
#123 6th St. Melbourne, FL 32904