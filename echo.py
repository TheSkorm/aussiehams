import boto3

SKILL_NAME = "Australian Ham"
HELP_MESSAGE = "Australian callsign lookup from ACMA RADCOM database. For example you can ask - Who is Victor Kilo Three Foxtrot Uniform Charlie?  What callsign would you like to look up today?"
HELP_REPROMPT = HELP_MESSAGE
STOP_MESSAGE = "Goodbye!"
FALLBACK_MESSAGE = "At the moment I only lookup callsigns, you can ask me who a call sign is!"
FALLBACK_REPROMPT = HELP_REPROMPT
OPEN_MESSAGE = "What callsign would you like to lookup?"

TABLE="australiancallsigns"

db = boto3.client('sdb')

# --------------- App entry point -----------------

def lambda_handler(event, context):
    """  App entry point  """

    #print(event)

    if event['session']['new']:
        on_session_started()

    if event['request']['type'] == "LaunchRequest":
        return on_launch(event['request'])
    elif event['request']['type'] == "IntentRequest":
        return on_intent(event['request'], event['session'])
    elif event['request']['type'] == "SessionEndedRequest":
        return on_session_ended()

# --------------- Response handlers -----------------

def on_intent(request, session):
    """ called on receipt of an Intent  """

    intent_name = request['intent']['name']
    # process the intents
    if intent_name == "lookup":
        return get_lookup_response(request['intent']['slots'])
    elif intent_name == "AMAZON.HelpIntent":
        return get_help_response()
    elif intent_name == "AMAZON.StopIntent":
        return get_stop_response()
    elif intent_name == "AMAZON.CancelIntent":
        return get_stop_response()
    elif intent_name == "AMAZON.FallbackIntent":
        return get_fallback_response()
    else:
        print("invalid Intent reply with help")
        return get_help_response()

def get_lookup_response(slots):
    """ get and return a random fact """
    callsign=""
    try:
        callsign += slots['countrya']['value'][0]
    except:
        pass
    try:
        callsign += slots['countryb']['value'][0]
    except:
        pass
    try:
        callsign += slots['number']['value']
    except:
        pass
    try:
        callsign += slots['calla']['value'][0]
    except:
        pass
    try:
        callsign += slots['callb']['value'][0]
    except:
        pass
    try:
        callsign += slots['callc']['value'][0]
    except:
        pass
    try:
        callsign += slots['calld']['value'][0]
    except:
        pass
    callsign = callsign.upper()
    
    results = db.get_attributes(
        DomainName=TABLE,
        ItemName=callsign,
        ConsistentRead=False,
        AttributeNames=["name","suburb","state","type"]
    )
    prettyCall =  " ".join(list(callsign.lower()))
    try:
        attrs = {v['Name']: v['Value'] for v in results['Attributes']}
    except KeyError:
        speechOutput = "I'm sorry but I couldn't find " + prettyCall + " in the database."
        return response(speech_response_with_card(SKILL_NAME, speechOutput,
                                                          speechOutput, True))
    attrs['state'] = attrs['state'].replace("QLD", "Queensland")
    attrs['state'] = attrs['state'].replace("NSW", "New South Whales")
    attrs['state'] = attrs['state'].replace("SA", "South Australia")
    attrs['state'] = attrs['state'].replace("VIC", "Victoria")
    attrs['state'] = attrs['state'].replace("WA", "Western Australia")
    attrs['state'] = attrs['state'].replace("NT", "Northern Terrority")
    attrs['state'] = attrs['state'].replace("TAS", "Tasmania")
    attrs['state'] = attrs['state'].replace("ACT", "Australian Capitial Terrority")
    attrs['state'] = attrs['state'].replace("NOR", "Norfolk Island")
    cardcontent = '{} is {}, an {} license holder whose postal address is {}, {}'.format(callsign.upper(), attrs['name'], attrs['type'], attrs['suburb'],attrs['state'])
    speechOutput = '{}. is {}, an {} license holder whose postal address is {}, {}'.format(prettyCall, attrs['name'], attrs['type'], attrs['suburb'],attrs['state'])

    return response(speech_response_with_card(SKILL_NAME, speechOutput,
                                                          cardcontent, True))


def get_help_response():
    """ get and return the help string  """

    speech_message = HELP_MESSAGE
    return response(speech_response_prompt(speech_message,
                                                       speech_message, False))
def get_open_response():
    """ get and return the open string  """

    speech_message = OPEN_MESSAGE
    return response(speech_response_prompt(speech_message,
                                                       speech_message, False))                                                
def get_launch_response():
    """ get and return the help string  """

    return get_open_response()

def get_stop_response():
    """ end the session, user wants to quit the game """

    speech_output = STOP_MESSAGE
    return response(speech_response(speech_output, True))

def get_fallback_response():
    """ end the session, user wants to quit the game """

    speech_output = FALLBACK_MESSAGE
    return response(speech_response(speech_output, False))

def on_session_started():
    """" called when the session starts  """
    #print("on_session_started")

def on_session_ended():
    """ called on session ends """
    #print("on_session_ended")

def on_launch(request):
    """ called on Launch, we reply with a launch message  """

    return get_launch_response()


# --------------- Speech response handlers -----------------

def speech_response(output, endsession):
    """  create a simple json response  """
    return {
        'outputSpeech': {
            'type': 'PlainText',
            'text': output
        },
        'shouldEndSession': endsession
    }

def dialog_response(endsession):
    """  create a simple json response with card """

    return {
        'version': '1.0',
        'response':{
            'directives': [
                {
                    'type': 'Dialog.Delegate'
                }
            ],
            'shouldEndSession': endsession
        }
    }

def speech_response_with_card(title, output, cardcontent, endsession):
    """  create a simple json response with card """

    return {
        'card': {
            'type': 'Simple',
            'title': title,
            'content': cardcontent
        },
        'outputSpeech': {
            'type': 'PlainText',
            'text': output
        },
        'shouldEndSession': endsession
    }

def response_ssml_text_and_prompt(output, endsession, reprompt_text):
    """ create a Ssml response with prompt  """

    return {
        'outputSpeech': {
            'type': 'SSML',
            'ssml': "<speak>" +output +"</speak>"
        },
        'reprompt': {
            'outputSpeech': {
                'type': 'SSML',
                'ssml': "<speak>" +reprompt_text +"</speak>"
            }
        },
        'shouldEndSession': endsession
    }

def speech_response_prompt(output, reprompt_text, endsession):
    """ create a simple json response with a prompt """

    return {
        'outputSpeech': {
            'type': 'PlainText',
            'text': output
        },
        'reprompt': {
            'outputSpeech': {
                'type': 'PlainText',
                'text': reprompt_text
            }
        },
        'shouldEndSession': endsession
    }

def response(speech_message):
    """ create a simple json response  """
    return {
        'version': '1.0',
        'response': speech_message
    }