from utility import config

# TODO - Move forecast.py methods into this file

def custom_id(view: str, id: int) -> str:
    """ Return the view with the id """
    return f"{config.BOT_NAME}:{view}:{id}"