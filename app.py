import streamlit as st
import requests
from langchain import OpenAI
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain.llms import OpenAI

# Constants for API keys and endpoints
ORS_API_KEY = '5b3ce3597851110001cf62487c78f6711091486ebd9ad47105c34fe3'
NOMINATIM_ENDPOINT = 'https://nominatim.openstreetmap.org/search'
OVERPASS_ENDPOINT = 'https://overpass-api.de/api/interpreter'
ORS_ENDPOINT = 'https://api.openrouteservice.org/v2/directions/driving-car'

# Function to get city coordinates
def get_city_coordinates(city_name):
    params = {
        'q': city_name,
        'format': 'json',
        'addressdetails': 1,
        'limit': 1
    }
    headers = {
        'User-Agent': 'TravelGuideApp/1.0 (kalekardarshan5@gmail.com)'
    }
    response = requests.get(NOMINATIM_ENDPOINT, params=params, headers=headers)
    
    # Check if the response is valid
    if response.status_code != 200:
        st.error(f"Error fetching coordinates: {response.status_code}")
        return None, None
    
    try:
        data = response.json()
    except ValueError:
        st.error("Error decoding JSON from coordinates API response.")
        return None, None
    
    if not data:
        return None, None
    
    lat = data[0]['lat']
    lon = data[0]['lon']
    
    return lat, lon

# Function to get nearby places from Overpass API
def get_nearby_places(lat, lon, place_type):
    type_mapping = {
        'restaurant': 'node["amenity"="restaurant"]',
        'hotel': 'node["tourism"="hotel"]',
        'station': 'node["railway"="station"]',
    }
    
    query = f"""
    [out:json];
    (
      {type_mapping.get(place_type)}(around:5000,{lat},{lon});
    );
    out body;
    """
    
    response = requests.get(OVERPASS_ENDPOINT, params={'data': query})
    
    # Check if the response is valid
    if response.status_code != 200:
        st.error(f"Error fetching nearby places: {response.status_code}")
        return []
    
    try:
        data = response.json()
    except ValueError:
        st.error("Error decoding JSON from Overpass API response.")
        return []
    
    places = data.get('elements', [])
    
    return [place['tags'].get('name', 'Unnamed') for place in places]

# Function to get directions using OpenRouteService API
def get_directions(lat1, lon1, lat2, lon2):
    body = {
        'coordinates': [[lon1, lat1], [lon2, lat2]],
        'format': 'json'
    }
    headers = {
        'Authorization': ORS_API_KEY,
        'Content-Type': 'application/json'
    }
    response = requests.post(ORS_ENDPOINT, json=body, headers=headers)
    
    # Check if the response is valid
    if response.status_code != 200:
        st.error(f"Error fetching directions: {response.status_code}")
        return None
    
    try:
        data = response.json()
    except ValueError:
        st.error("Error decoding JSON from OpenRouteService API response.")
        return None
    
    if 'routes' not in data or not data['routes']:
        return None
    
    directions = data['routes'][0]['segments'][0]['steps']
    route_instructions = []
    for step in directions:
        route_instructions.append(step['instruction'])
    
    return route_instructions

# Streamlit application
def main():
    st.title("Travel Guide Chatbot")

    city_name = st.text_input("Enter City Name:")
    
    if st.button("Get Info"):
        if not city_name:
            st.write("Please enter a city name.")
        else:
            st.write("Fetching data, please wait...")
            lat, lon = get_city_coordinates(city_name)
            if lat is None or lon is None:
                st.write("City not found or API request failed.")
            else:
                restaurants = get_nearby_places(lat, lon, 'restaurant')
                hotels = get_nearby_places(lat, lon, 'hotel')
                stations = get_nearby_places(lat, lon, 'station')
                
                st.write(f"City: {city_name}")
                st.write("Nearby Restaurants:")
                st.write(", ".join(restaurants))
                st.write("Nearby Hotels:")
                st.write(", ".join(hotels))
                st.write("Nearby Stations:")
                st.write(", ".join(stations))
                
    st.write("----")
    st.header("Get Directions")
    start_place = st.text_input("Enter Start Place:")
    end_place = st.text_input("Enter End Place:")
    
    if st.button("Get Directions"):
        if not start_place or not end_place:
            st.write("Please enter both start and end places.")
        else:
            st.write("Fetching directions, please wait...")
            start_lat, start_lon = get_city_coordinates(start_place)
            end_lat, end_lon = get_city_coordinates(end_place)
            if start_lat is None or start_lon is None or end_lat is None or end_lon is None:
                st.write("Start or end place not found or API request failed.")
            else:
                directions = get_directions(start_lat, start_lon, end_lat, end_lon)
                if directions is None:
                    st.write("Directions not found or API request failed.")
                else:
                    st.write("Directions:")
                    for instruction in directions:
                        st.write(instruction)

if __name__ == "__main__":
    main()
