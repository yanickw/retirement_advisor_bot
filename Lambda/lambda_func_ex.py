### Required Libraries ###
from datetime import datetime
from dateutil.relativedelta import relativedelta
import json

# add logging to help with troubleshooting lambda function
import logging

# get root logger and set logging level to INFO
logger = logging.getLogger()
logger.setLevel(logging.INFO)

### Functionality Helper Functions ###
def parse_int(n):
    """
    Securely converts a non-integer value to integer.
    """
    try:
        return int(n)
    except ValueError:
        logging.error(f"{n} is not a valid int")
        return float("nan")


def build_validation_result(is_valid, violated_slot, message_content):
    """
    Define a result message structured as Lex response.
    """
    if message_content is None:
        return {"isValid": is_valid, "violatedSlot": violated_slot}

    return {
        "isValid": is_valid,
        "violatedSlot": violated_slot,
        "message": {"contentType": "PlainText", "content": message_content},
    }


### Dialog Actions Helper Functions ###
def get_slots(intent_request):
    """
    Fetch all the slots and their values from the current intent.
    """
    return intent_request["currentIntent"]["slots"]


def elicit_slot(session_attributes, intent_name, slots, slot_to_elicit, message):
    """
    Defines an elicit slot type response.
    """
    logger.info(f"Eliciting {slot_to_elicit} due to {message}")
    return {
        "sessionAttributes": session_attributes,
        "dialogAction": {
            "type": "ElicitSlot",
            "intentName": intent_name,
            "slots": slots,
            "slotToElicit": slot_to_elicit,
            "message": message,
        },
    }


def delegate(session_attributes, slots):
    """
    Defines a delegate slot type response.
    """

    return {
        "sessionAttributes": session_attributes,
        "dialogAction": {"type": "Delegate", "slots": slots},
    }


def close(session_attributes, fulfillment_state, message):
    """
    Defines a close slot type response.
    """

    response = {
        "sessionAttributes": session_attributes,
        "dialogAction": {
            "type": "Close",
            "fulfillmentState": fulfillment_state,
            "message": message,
        },
    }

    return response


"""
Step 3: Enhance the Robo Advisor with an Amazon Lambda Function
In this section, you will create an Amazon Lambda function that will validate the data provided by the user on the Robo Advisor.
1. Start by creating a new Lambda function from scratch and name it `recommendPortfolio`. Select Python 3.7 as runtime.
2. In the Lambda function code editor, continue by deleting the AWS generated default lines of code, then paste in the starter code provided in `lambda_function.py`.
3. Complete the `recommend_portfolio()` function by adding these validation rules:
    * The `age` should be greater than zero and less than 65.
    * The `investment_amount` should be equal to or greater than 5000.
4. Once the intent is fulfilled, the bot should respond with an investment recommendation based on the selected risk level as follows:
    * **none:** "100% bonds (AGG), 0% equities (SPY)"
    * **low:** "60% bonds (AGG), 40% equities (SPY)"
    * **medium:** "40% bonds (AGG), 60% equities (SPY)"
    * **high:** "20% bonds (AGG), 80% equities (SPY)"
> **Hint:** Be creative while coding your solution, you can have all the code on the `recommend_portfolio()` function, or you can split the functionality across different functions, put your Python coding skills in action!
5. Once you finish coding your Lambda function, test it using the sample test events provided for this Challenge.
6. After successfully testing your code, open the Amazon Lex Console and navigate to the `recommendPortfolio` bot configuration, integrate your new Lambda function by selecting it in the “Lambda initialization and validation” and “Fulfillment” sections.
7. Build your bot, and test it with valid and invalid data for the slots.
"""

# define constants
minimum_age = 0
maximum_age = 65
minumum_amount = 5000
valid_risk_levels = ['none','low','medium','high']

def valid_age(age):
    valid = True #default

    if age is None:
        valid = False
    else:
        age = parse_int(age)
        if age == float("nan") or age < minimum_age or age > maximum_age:
            valid = False

    if not valid:
        # age is not valid
        message = f"{age} is not a suported age.  Age must be > {minimum_age} and < {maximum_age}."
        logger.warning(message)
        return build_validation_result(
            False,
            "age",
            f"{message} Please enter a valid age."
        )

    # A True results is returned if age is valid
    return build_validation_result(True, None, None)
        
def valid_investment(amount):
    valid = True #default

    if amount is None:
        valid = False
    else:
        amount = parse_int(amount)
        if amount == float("nan") or amount < minumum_amount:
            valid = False

    if not valid:
        # investment amount is not valid
        message = f"{amount} is not a suported investment amount.  Investment amount must be >= {minumum_amount}."
        logger.warning(message)
        return build_validation_result(
            False,
            "investmentAmount",
            f"{message} Please enter a valid investment amount."
        )

    # A True results is returned if amount is valid
    return build_validation_result(True, None, None)

def valid_risk_level(risk_level):
    if risk_level is None or risk_level.lower() not in valid_risk_levels:
        # risk_level amount is not valid
        message = f"{risk_level} is not a valid risk level.  Select one of the following: {','.join(valid_risk_levels)}"
        logger.warning(message)
        return build_validation_result(
            False,
            "riskLevel",
            f"{message} Please enter a valid risk level."
        )

    # A True results is returned if risk_level is valid
    return build_validation_result(True, None, None)

def get_investment_recommendation(risk_level):
    """
    * **none:** "100% bonds (AGG), 0% equities (SPY)"
    * **low:** "60% bonds (AGG), 40% equities (SPY)"
    * **medium:** "40% bonds (AGG), 60% equities (SPY)"
    * **high:** "20% bonds (AGG), 80% equities (SPY)"    
    """
    risk_level = risk_level.lower()
    recommendation = "100% bonds (AGG), 0% equities (SPY)" # default
    if risk_level == 'low':
        recommendation = "60% bonds (AGG), 40% equities (SPY)"
    elif risk_level == 'medium':
        recommendation = "40% bonds (AGG), 60% equities (SPY)"
    elif risk_level == 'high':
        recommendation = "20% bonds (AGG), 80% equities (SPY)"
    return recommendation

### Intents Handlers ###
def recommend_portfolio(intent_request):
    """
    Performs dialog management and fulfillment for recommending a portfolio.
    """

    first_name = get_slots(intent_request)["firstName"]
    age = get_slots(intent_request)["age"]
    investment_amount = get_slots(intent_request)["investmentAmount"]
    risk_level = get_slots(intent_request)["riskLevel"]
    source = intent_request["invocationSource"]

    # add logging to confirm slots and source from intent
    logger.info(f"source: {source}")
    logger.info(f"first_name: {first_name}")
    logger.info(f"age: {age}")
    logger.info(f"investment_amount: {investment_amount}")
    logger.info(f"risk_level: {risk_level}")

    if source == "DialogCodeHook":
        # This code performs basic validation on the supplied input slots.

        # Gets all the slots
        slots = get_slots(intent_request)
        logger.info(f"slots = {slots}")

        validation_result = valid_age(age)
        if not validation_result['isValid']:
            # Returns an elicitSlot dialog to request new data for the invalid slot
            return elicit_slot(
                intent_request["sessionAttributes"],
                intent_request["currentIntent"]["name"],
                slots,
                validation_result["violatedSlot"],
                validation_result["message"],
            ) 

        validation_result = valid_investment(investment_amount)
        if not validation_result['isValid']:
            # Returns an elicitSlot dialog to request new data for the invalid slot
            return elicit_slot(
                intent_request["sessionAttributes"],
                intent_request["currentIntent"]["name"],
                slots,
                validation_result["violatedSlot"],
                validation_result["message"],
            ) 

        validation_result = valid_risk_level(risk_level)
        if not validation_result['isValid']:
            # Returns an elicitSlot dialog to request new data for the invalid slot
            return elicit_slot(
                intent_request["sessionAttributes"],
                intent_request["currentIntent"]["name"],
                slots,
                validation_result["violatedSlot"],
                validation_result["message"],
            ) 

        # Fetch current session attributes
        output_session_attributes = intent_request["sessionAttributes"]
        logger.info(f"output_session_attributes = {output_session_attributes}")

        # Once all slots are valid, a delegate dialog is returned to Lex to choose the next course of action.
        return delegate(output_session_attributes, get_slots(intent_request))

    # intent ready for fultillment
    investment_recommendation = get_investment_recommendation(risk_level)
    logger.info(f"investment_recommendation = {investment_recommendation}")

    # Return a message with conversion's result.
    return close(
        intent_request["sessionAttributes"],
        "Fulfilled",
        {
            "contentType": "PlainText",
            "content": f"""{first_name}, based on your {risk_level} risk tolerance, we recommend the following portfolio 
            {investment_recommendation}
            """,
        },
    )


### Intents Dispatcher ###
def dispatch(intent_request):
    """
    Called when the user specifies an intent for this bot.
    """

    intent_name = intent_request["currentIntent"]["name"]
    logger.info(f"intent_name = {intent_name}")

    # Dispatch to bot's intent handlers
    if intent_name == "recommendPortfolio":
        return recommend_portfolio(intent_request)

    raise Exception("Intent with name " + intent_name + " not supported")


### Main Handler ###
def lambda_handler(event, context):
    """
    Route the incoming request based on intent.
    The JSON body of the request is provided in the event slot.
    """
    logger.info(f"event: \n{json.dumps(event)}")
    return dispatch(event)
Footer
© 2022 GitHub, Inc.
Footer navigation
Terms
Privacy
Security
Status
Docs
Contact GitHub
Pricing
API
Training
Blog
About
