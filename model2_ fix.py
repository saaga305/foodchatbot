from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import db_helper
import generic_helper


def process_intent(intent, parameters, session_id):
    if intent == "order.add- context; ongoing -order":
        return add_to_order(parameters, session_id)
    elif intent == "order.remove - context; ongoing -order":
        return remove_from_order(parameters, session_id)
    elif intent == "order.complete - context: ongoing-order":
        return complete_order(parameters, session_id)
    elif intent == "track.order - context: ongoing -tracking":
        return track_order(parameters, session_id)
    # Handle other intents here
    # ...


app = FastAPI()

inprogress_orders = {}

@app.post("/")  # Use @app.post("/") to handle POST requests
async def handle_request(request: Request):
    # Retrieve the JSON data from the request
    payload = await request.json()

    # Extract the necessary information from the payload
    # based on the structure of the WebhookRequest from Dialogflow
    intent = payload['queryResult']['intent']['displayName']
    parameters = payload['queryResult']['parameters']
    output_contexts = payload['queryResult']['outputContexts']

    session_id = generic_helper.extract_session_id(output_contexts[0]['name'])

    # Check if the user wants to start a new order
    if intent == 'new.order':
        # Clear the old conversation and start a new order
        inprogress_orders[session_id] = {}
        fulfillment_text = "Sure, let's start a new order. What would you like to order?"
    else:
        # Continue the existing conversation
        fulfillment_text = process_intent(intent, parameters, session_id)

    return JSONResponse(content={"fulfillmentText": fulfillment_text})
def remove_from_order(parameters: dict, session_id: str):
    if session_id not in inprogress_orders:
        return JSONResponse(content={
            "fulfillmentText": "I'm having a  trouble finding your order. Sorry! Can you place a new order"
        })


    current_order = inprogress_orders[session_id]
    food_items = parameters["food-item1"]


    removed_items = []
    no_such_items = []

    for item in food_items:
        if item not in current_order:
            no_such_items.append(item)
        else:
            removed_items.append(item)
            del current_order[item]

    if len(removed_items) > 0:
        fulfillment_text = f'Removed {",".join(removed_items)} from your order'


    if len(no_such_items) > 0:
        fulfillment_text = f'Your current order does not have {",".join(no_such_items)}'

    if len(current_order.keys()) == 0:
        fulfillment_text += "Your order is empty!"

    else:
        order_str =  generic_helper.get_str_from_food_dict(current_order)
        fulfillment_text += f" Here is what is left in your order: {order_str}"

    return JSONResponse(content={
        "fulfillmentText": fulfillment_text
    })


def add_to_order(parameters: dict, session_id: str):
    food_items = parameters["food-item1"]
    quantities = parameters["number"]

    if len(food_items) != len(quantities):
        fulfillment_text = "Sorry I didnt understand. Can you please specify food items and quantity clearly?"
    else:
        new_food_dict = dict(zip(food_items, quantities))

        if session_id in inprogress_orders:
            current_food_dict = inprogress_orders[session_id]
            current_food_dict.update(new_food_dict)
            inprogress_orders[session_id] =  current_food_dict
        else:
            inprogress_orders[session_id] = new_food_dict


        order_str = generic_helper.get_str_from_food_dict(inprogress_orders[session_id])
        fulfillment_text  = f"So far you have:  {order_str}. Do you need anything else?"


    return JSONResponse(content={
        "fulfillmentText": fulfillment_text
    })


def complete_order(parameters: dict, session_id: str):
    if session_id not in inprogress_orders:
        fulfillment_text = "I'm having a trouble finding your order. Sorry! Can you place a new order  please? "
    else:
        order = inprogress_orders[session_id]
        order_id = save_to_db(order)

        if order_id == -1:
            fulfillment_text = "Sorry, I coulnt process your order due to a backend error. " \
                                "Please place a new order again"

        else:
            order_total = db_helper.get_total_order_price(order_id)
            fulfillment_text = f"Awesome, We have placed your order. " \
                                f"Here is your order id # {order_id}. " \
                                f"Your order total is {order_total} which you can pay at the time "

        del inprogress_orders[session_id]

    return JSONResponse(content={
        "fulfillmentText": fulfillment_text
    })
def save_to_db(order: dict):
    #order = {"pizza":2, "chole":1}
    next_order_id = db_helper.get_next_order_id()


    for food_item, quantity in order.items():
        rcode = db_helper.insert_order_item(
            food_item,
            quantity,
            next_order_id
        )

        if rcode == -1:
            return  -1

    db_helper.insert_order_tracking(next_order_id, "in progress ")

    return next_order_id
def track_order(parameters: dict, session_id: str):
    order_id = int(parameters.get('order_id', 0)) # note change number to order id

    order_status =  db_helper.get_order_status(order_id)

    if order_status:
        fulfillment_text = f"The order status for order id: {order_id} is: {order_status}"
    else:
        fulfillment_text = f"No order found with order id: {order_id}"



    return JSONResponse(content={
        "fulfillmentText": fulfillment_text
    })








