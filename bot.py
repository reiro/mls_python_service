from textblob import TextBlob
from textblob.np_extractors import ConllExtractor
from agent import *
import code

categories = ['greetings', 'actions', 'beds', 'baths', 'max_price', 'address']


def get_blob_messages(message):
	blob = TextBlob(message)

	if len(blob.words) > 1:
		messages = blob.ngrams(n=2) + blob.ngrams(n=3)
	else:
		messages = blob.ngrams(n=1)

	return messages

def prepare_result(result):
	return ' '.join([str(x) for x in result])

def greetings_ensure(result, agent):
	if not agent['has_greetings']:
		result.insert(0, greetings_wrap(''))
		agent['has_greetings'] = True

def next_category(agent):
	for category in categories:
		if not agent['has_' + category]:
			return category
			break

def check_if_integer(statements):
	return len(statements) == 1 and isfloat(statements[0][2])

def result_push(result, category, statement, agent):
	agent[category] = statement
	agent['has_' + category] = True

	sentence = wrap_category(category, statement) # add text to parsed params
	result.append(sentence)

def perform(params):
	result = []
	groups = { 'greetings':[], 'actions':[], 'beds':[], 'baths':[], 'min_price':[], 'max_price':[], 'address':[] }
	agent = params['agent']
	messages = get_blob_messages(params['message'])

	statements = analyze_messages(messages, sets, fuzz.partial_ratio)
	statements_hash = group_by_category(statements, groups)
	
	if next_category(agent) == 'address':
		address = parse_address(params['message'])
		# code.interact(local=dict(globals(), **locals()))
		if 'StateName' in address:
			agent['has_address'] = True
			for prop in address:
				agent["address"][underscore(prop)] = address[prop]

	print agent

	if next_category(agent) == 'max_price':
		prices = parse_price(messages)
		if len(prices) == 2:
			result_push(result, 'min_price', prices[0], agent)
			result_push(result, 'max_price', prices[1], agent)
		elif len(prices) == 1:
			result_push(result, 'max_price', prices[0], agent)

	if check_if_integer(statements):
		result_push(result, next_category(agent), statements[0][2], agent)
	else:
		for category in categories:
			statements = statements_hash[category] # array of typles ('greetings', 100, 'Good day')

			if statements:
				response = answer_category(category, statements) # array of parsed integers or data

				if len(response) > 0 and not agent['has_' + category]:
					result_push(result, category, response[0], agent)

	greetings_ensure(result, agent)
  	res_message = prepare_result(result)

  	if agent['has_beds'] or agent['has_baths'] or agent['has_min_price'] or agent['has_max_price'] or agent['has_address']:
  		agent['has_general'] = True

	if agent['has_actions'] and not agent['has_general']:
		question = questions_category('general')
		agent['has_general'] = True
	else:
		print next_category(agent)
		question = questions_category(next_category(agent))

  	print question
  	print result

	return { 'message': res_message, 'question': question, 'agent': agent }
