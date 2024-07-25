import re

def extract_session_id(session_str: str):
    import re
    match = re.search(r"/sessions/(.*?)/contexts/", session_str)
    if match:
        extracted_string = match.group(1)
        return extracted_string

    return ""

def get_str_from_food_dict(food_dict: dict):
    result = ", ".join([f"{int(value)} {key}" for key, value in food_dict.items()])
    return result

if __name__ == "__main__":
    print(get_str_from_food_dict({"samosa":2, "chhole": 5}))
    print(extract_session_id("projects/mira-chatbot-for-food-del-d9bj/agent/sessions/123/contexts/ongoing-order"))