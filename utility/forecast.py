# forecast.py
from geopy.geocoders import Nominatim
from utility.config import EMAIL
from typing import Union
from logger import logger
import requests
import json


points_headers = {
    'User-Agent': 'Tarleton Discord Bot Weather Service Display',
    'Accept': 'application/geo-json',
    'From': EMAIL,
}


def geocode(client_location) -> Union[list, None]:
    """ Get latitude and longitude of desired location [city, state] """
    geolocator = Nominatim(user_agent=points_headers['User-Agent'])
    location = geolocator.geocode(client_location)
    if location == None:
        return None
    loc = [location.latitude, location.longitude]
    return loc


def get_gridpoints(location) -> Union[str, None]:
    """ Query weather.gov API for information related to lat/lon, retreived as json """
    client_location = geocode(location)
    try:
        logger.info("https://api.weather.gov/points/{0[0]},{0[1]}".format(client_location))
        points = requests.get(url="https://api.weather.gov/points/{0[0]},{0[1]}".format(client_location), headers=points_headers)
        package = json.loads(points.text)
        url = package["properties"]["forecast"]
    except requests.HTTPError as http_error:
        logger.critical(f"Error occurred while obtaining grid points: {http_error}")
        return None
    return url


def get_forecast(location) -> Union[str, None]:
    """ Query weather.gov API for forecast using url obtained from previous API call """
    forecast_url = get_gridpoints(location)
    if forecast_url == None:
        return None
    try:
        url_data = requests.get(url=forecast_url, headers=points_headers)
        json_data = json.loads(url_data.text)
        forecast_data = json_data["properties"]["periods"]
        return forecast_data
    except requests.HTTPError as http_error:
        logger.critical(f"Exception occurred while obtaining forecast: {http_error}")


def get_forecast_hourly(location) -> Union[str, None]:
    """ Query weather.gov API for hourly forecast using appended url obtained from previous API call """
    forecast_url = get_gridpoints(location)
    if forecast_url == None:
        return None
    try:
        url_data = requests.get(url=forecast_url+"/hourly", headers=points_headers)
        json_data = json.loads(url_data.text)
        forecast_data = json_data["properties"]["periods"]
        return forecast_data
    except requests.HTTPError as http_error:
        logger.critical(f"Exception occurred while optaining hourly forecast: {http_error}")


def get_all_alerts(location) -> Union[str, None]:
    """ Query weather.gov API for ALL active weather alerts for passed state - ex. TX """
    try:
        url_data = requests.get(url="https://api.weather.gov/alerts/active/area/{0}".format(location))
        json_data = json.loads(url_data.text)
        alert_data = json_data["features"]
        return alert_data
    except requests.HTTPError as http_error:
        logger.critical(f"Exception occurred while obtaining all weather alerts: {http_error}")


def get_county_alerts(location) -> Union[str, None]:
    """ Query weather.gov API for specific county active weather alerts for passed city, state """
    client_location = geocode(location)
    try:
        points = requests.get(url="https://api.weather.gov/points/{0[0]},{0[1]}".format(client_location), headers=points_headers)
        logger.info("https://api.weather.gov/points/{0[0]},{0[1]}".format(client_location))
        package = json.loads(points.text)
        county_ID = package["properties"]["county"].strip('https://api.weather.gov/zones/county/')
        logger.info(f"County ID : {county_ID}")
        alerts = requests.get(url=f"https://api.weather.gov/alerts/active?zone={county_ID}", headers=points_headers)
        logger.info(f"https://api.weather.gov/alerts/active?zone={county_ID}")
        alerts_data = json.loads(alerts.text)
    except requests.HTTPError as http_error:
        logger.critical(f"Exception occurred while obtaining county alerts: {http_error}")
        return None
    except json.JSONDecodeError as json_error:
        logger.critical(f"Invalid type encountered while unpackaging: {json_error}")
        return None
    return alerts_data["features"]