# Import required packages
from geopy.geocoders import ArcGIS
import folium
import streamlit as st
from streamlit_tags import st_tags
from streamlit_folium import st_folium
import pandas as pd
import geopandas as gpd
import pytz
import timezonefinder
from datetime import datetime
from dotenv import load_dotenv # pip install python-dotenv. This takes environment variables from .env
import os
import requests

# Load API key from the environment variables file
load_dotenv()
API_KEY = os.getenv("API_KEY")


# -------------- SETTINGS ----------------------------
page_title = "Geolocalisation and timezone in world map indicator"
layout = "centered"
# ----------------------------------------------------


def main():
    st.set_page_config(page_title = page_title, layout = layout)
    st.title(page_title)

if __name__ == '__main__':
    main()

# --- Hide Streamlit Style ---
hide_st_style = """
                <style>
                #MainMenu {Visibility: hidden;}
                footer {Visibility: hidden;}
                header {Visibility: hidden;}
                </style>
"""
st.markdown(hide_st_style, unsafe_allow_html=True)

nom=ArcGIS()

# Function to get weather for the given location
def getWeather(lat, lng):

    # weather info from open weather map api
    api = "https://api.openweathermap.org/data/2.5/weather?lat="\
        +str(lat)\
        +"&lon="+str(lng)\
        +"&units=metric"\
        +"&appid="+str(API_KEY)
    
    json_data = requests.get(api).json()

    # Current temperature
    temp = json_data['main']['temp']
    pressure = json_data['main']['pressure']
    humidity = json_data['main']['humidity']
    wind = json_data['wind']['speed'] 
    description = json_data['weather'][0]['description']

    return temp, pressure, humidity, wind, description

# Input place name as list in streamlit, maximum tabs is limited to 15
place_name = st_tags(
    label='## Enter place name:',
    text='Press enter to add more',
    value=['Chennai', 'Paris', 'Athens'],
    maxtags = 15,
    key='1')

# Convert List to a DataFrame
place_df = pd.DataFrame(place_name)
  
place_df.columns = ['placename']
  
# Display dataframe after renaming the columns
#print(place_df.columns)

place_df['coordinates']=place_df['placename'].apply(nom.geocode)
#parcreg_df2['coordinates'].values

# Using lambda function to set the latitude of longitude in parc regional dataframe
place_df['latitude'] = place_df['coordinates'].apply(lambda x: x.latitude)
place_df['longitude'] = place_df['coordinates'].apply(lambda x: x.longitude)
place_df = place_df.reset_index()  # make sure indexes pair with number of rows

tf = timezonefinder.TimezoneFinder()

tz_lst, time_lst = [], []

temp_lst = []
pressure_lst = []
humidity_lst = []
wind_lst = []
description_lst = []

for row in place_df.itertuples(index=False):
    lng=row[place_df.columns.get_loc('longitude')]
    lat=row[place_df.columns.get_loc('latitude')]
    # From the lat/long, get the tz-database-style time zone name (e.g. 'Europe/Paris') or None
    timezone = tf.certain_timezone_at(lng=row[place_df.columns.get_loc('longitude')],\
                                       lat=row[place_df.columns.get_loc('latitude')])
    tz_lst.append(timezone)
    
    timezone = pytz.timezone(timezone)
    local_time = datetime.now(timezone)
    current_time = local_time.strftime("%I:%M %p")    
    time_lst.append(current_time)
    
    # Call function to get weather deatils such as temperature, pressure, wind speed, humidity and weather description
    temp, pressure, wind, humidity, description = getWeather(lat, lng)

    temp_lst.append(temp)
    pressure_lst.append(pressure)
    wind_lst.append(wind)
    humidity_lst.append(humidity)
    description_lst.append(description)

place_df['timezone'] = tz_lst
place_df['current time'] = time_lst 
place_df['temperature'] = temp_lst
place_df['pressure'] = pressure_lst 
place_df['wind speed'] = wind_lst
place_df['humidity'] = humidity_lst
place_df['description'] = description_lst

"---"
st.write('Place name with coordinates, timezone, current time and weather details in data frame')
st.write(place_df)

place_list = place_df[['placename', 'latitude', 'longitude',\
                        'timezone', 'current time', 'temperature',\
                            'pressure', 'wind speed', 'humidity', 'description']].values.tolist()

# Plotting place name in the map 
# Below are the latitude and longitude of default location, in this case it's set to Chennai
m = folium.Map(location=[13.0838, 80.2826], zoom_start=2)
fg = folium.FeatureGroup(name = "Geolocation with weather details of places in world map")

"---"
st.write()
st.write('World map showing geo located coordinates and weather details of places')
for i in place_list:
    fg.add_child(
        folium.Marker(
            location=[i[1],i[2]],
            popup=f"{i[0]}\n {i[1]}°N\n {i[2]}°E\n {i[3]}\n {i[4]}\n {i[5]}°C\n pressure: {i[6]}hPa\n wind speed: {i[7]}m/s\n humidity: {i[8]}%\n description: {i[9]} ",
            icon=folium.Icon(color="blue")            
        )
    )

out = st_folium(
    m,
    feature_group_to_add=fg,
    width=1200,
    height=500,
)
