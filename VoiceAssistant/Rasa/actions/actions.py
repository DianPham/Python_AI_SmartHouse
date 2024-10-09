from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet, EventType, AllSlotsReset
from rasa_sdk.types import DomainDict
from rasa_sdk.events import UserUtteranceReverted
import requests
import re
import json
import Levenshtein
from datetime import datetime, timedelta
import calendar
from math import radians, sin, cos, sqrt, atan2
import geocoder

# Example using Spotify's API
import spotipy
from spotipy.oauth2 import SpotifyOAuth

# Initialize Spotify client
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id='fcb535d7568e400ebad08091fbee0027',
    client_secret='8128f7d68e50457fac477fb40253ae66',
    redirect_uri='http://localhost:5000/callback',
    scope='user-modify-playback-state,user-read-playback-state'))

# Load the knowledge base from the JSON file
knowledge_base_filename = "./knowledge_base.json"
with open(knowledge_base_filename, encoding="utf-8") as kb_file:
    knowledge_base = json.load(kb_file)

class ActionEndConversation(Action):
    def name(self) -> Text:
        return "action_end_conversation"

    def run(self, dispatcher, tracker, domain):
        dispatcher.utter_message(template="utter_end")
        return [UserUtteranceReverted()]


class ActionPlayTopSong(Action):

    def name(self) -> Text:
        return "action_play_top_song"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        top_playlist_result = sp.search(q='Top 50 - Global', type='playlist', limit=1)
        if top_playlist_result['playlists']['items']:
            playlist_uri = top_playlist_result['playlists']['items'][0]['uri']
            
            # Play the top 50 playlist
            sp.start_playback(context_uri=playlist_uri)
            dispatcher.utter_message(template="utter_turn_on_music")
        else:
            dispatcher.utter_message(template="utter_default_fallback")

        return [AllSlotsReset()]


# Function to calculate Word Error Rate (WER)
def word_error_rate(ref: str, hyp: str) -> float:
    return Levenshtein.distance(ref, hyp) / max(len(ref.split()), len(hyp.split()))

class ActionPlaySongWithArtist(Action):
    def name(self) -> str:
        return "action_play_song_with_artist"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: DomainDict) -> list:
        # Extract slots
        song = tracker.get_slot("song")
        artist = tracker.get_slot("artist")

        found_song, found_artist = self.match_with_knowledge_base(song, artist)
        response_text = ""

        # Step 1: If no match found in knowledge base, try verifying with Spotify
        if not found_song or (artist and not found_artist):
            found_song, found_artist = self.verify_with_spotify(song, artist)
            # Update knowledge base if matches found from Spotify
            if found_song:
                self.update_knowledge_base("songs", found_song)
            if found_artist:
                self.update_knowledge_base("artists", found_artist)

        # Step 2: Perform the final action based on found matches
        if found_song:
            # Play song using Spotify API
            if self.search_on_spotify(found_song, found_artist):
                response_text = f"Đang phát bài '{found_song}'"
                if found_artist:
                    response_text += f" của {found_artist}."
                dispatcher.utter_message(text=response_text)
            else:
                dispatcher.utter_message(template="utter_default_fallback")
        else:
            # Step 3: Fallback using regex extraction
            regex_extracted_song, regex_extracted_artist = self.regex_extractor(tracker.latest_message.get("text"))
            if regex_extracted_song or regex_extracted_artist:
                if regex_extracted_song:
                    response_text += f"Đang phát bài '{regex_extracted_song}'"
                    found_song = regex_extracted_song
                if regex_extracted_artist:
                    if regex_extracted_song:
                        response_text += " của "
                    response_text += f"{regex_extracted_artist}"
                    found_artist = regex_extracted_artist

                self.search_on_spotify(found_song, found_artist)
                dispatcher.utter_message(text=response_text)
            else:
                dispatcher.utter_message(text="Xin lỗi, em không thể tìm được bài hát hoặc ca sĩ này, xin hãy thử lại.")

        return [AllSlotsReset()]

    def match_with_knowledge_base(self, song: str, artist: str):
        found_song = None
        found_artist = None

        # Check song against knowledge base with WER
        if song:
            for known_song in knowledge_base["songs"]:
                if word_error_rate(known_song.lower(), song.lower()) < 0.2:
                    found_song = known_song
                    break

        # Check artist against knowledge base with WER
        if artist:
            for known_artist in knowledge_base["artists"]:
                if word_error_rate(known_artist.lower(), artist.lower()) < 0.2:
                    found_artist = known_artist
                    break

        return found_song, found_artist

    def verify_with_spotify(self, song: str, artist: str):
        print(song)
        print(artist)
        found_song = None
        found_artist = None

        # Search Spotify for the song
        if song:
            song_result = sp.search(q=f"track:{song}", type='track', limit=1)
            if song_result['tracks']['items']:
                found_song = song_result['tracks']['items'][0]['name'].lower()

        # Search Spotify for the artist
        if artist:
            artist_result = sp.search(q=f"artist:{artist}", type='artist', limit=1)
            if artist_result['artists']['items']:
                found_artist = artist_result['artists']['items'][0]['name'].lower()

        return found_song, found_artist

    def update_knowledge_base(self, category: str, new_entry: str):
        if new_entry not in knowledge_base[category]:
            knowledge_base[category].append(new_entry)

            # Save updated knowledge base to the JSON file
            with open(knowledge_base_filename, 'w', encoding='utf-8') as kb_file:
                json.dump(knowledge_base, kb_file, ensure_ascii=False, indent=4)

    def search_on_spotify(self, song: str, artist: str = None):
        print(song)
        print(artist)
        query = f"track:{song}"
        if artist:
            query += f" artist:{artist}"

        result = sp.search(q=query, type='track', limit=1)
        if result['tracks']['items']:
            track_uri = result['tracks']['items'][0]['uri']
            # Play the track
            sp.start_playback(uris=[track_uri])
            return True
        return False

    def regex_extractor(self, text: str):
        # Regex to extract possible song and artist names
        song_regex = r"bài ([^\n]+) của"
        artist_regex = r"của ([^\n]+)(?:\s+(?:đi|nha|em))?"

        extracted_song = None
        extracted_artist = None

        # Extract the song name
        song_match = re.search(song_regex, text, re.IGNORECASE)
        if song_match:
            extracted_song = song_match.group(1).strip()

        # Extract the artist name
        artist_match = re.search(artist_regex, text, re.IGNORECASE)
        if artist_match:
            extracted_artist = artist_match.group(1).strip()

        return extracted_song, extracted_artist

class ActionPlayArtistPlaylist(Action):

    def name(self) -> Text:
        return "action_play_artist"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:      
        artist = tracker.get_slot('artist')
        
        found_artist = self.match_with_knowledge_base( artist)
        
        if not found_artist:
            found_artist = self.verify_with_spotify(artist)
            # Update knowledge base if matches found from Spotify
            if found_artist:
                self.update_knowledge_base("artists", found_artist)
        
        # Step 2: Perform the final action based on found matches
        if found_artist:
            # Play song using Spotify API
            if self.search_on_spotify(found_artist):
                response_text = f"Đang phát nhạc của {found_artist}."
                dispatcher.utter_message(text=response_text)
            else:
                dispatcher.utter_message(template="utter_default_fallback")
        else:
            # Step 3: Fallback using regex extraction
            regex_extracted_artist = self.regex_extractor(tracker.latest_message.get("text"))
            if regex_extracted_artist:
                found_artist = regex_extracted_artist
                self.search_on_spotify( found_artist)
                dispatcher.utter_message(text=f"Đang phát nhạc của {found_artist}.")
            else:
                dispatcher.utter_message(text="Xin lỗi, em không thể tìm được ca sĩ này, xin hãy thử lại.")

        return [AllSlotsReset()]
    def match_with_knowledge_base(self, artist: str):
        found_artist = None

        # Check artist against knowledge base with WER
        if artist:
            for known_artist in knowledge_base["artists"]:
                if word_error_rate(known_artist.lower(), artist.lower()) < 0.2:
                    found_artist = known_artist
                    break

        return found_artist

    def verify_with_spotify(self, artist: str):
        
        print(artist)
        found_artist = None

        # Search Spotify for the artist
        if artist:
            artist_result = sp.search(q=f"artist:{artist}", type='artist', limit=1)
            if artist_result['artists']['items']:
                found_artist = artist_result['artists']['items'][0]['name'].lower()

        return found_artist

    def update_knowledge_base(self, category: str, new_entry: str):
        if new_entry not in knowledge_base[category]:
            knowledge_base[category].append(new_entry)

            # Save updated knowledge base to the JSON file
            with open(knowledge_base_filename, 'w', encoding='utf-8') as kb_file:
                json.dump(knowledge_base, kb_file, ensure_ascii=False, indent=4)

    def search_on_spotify(self, artist: str = None):
        print(artist)

        result = sp.search(q=f"artist:{artist}", type='artist', limit=1)
        if result['artists']['items']:
            track_uri = result['artists']['items'][0]['uri']
            print(track_uri)
            # Play the track
            sp.start_playback(context_uri=track_uri)
            return True
        return False

    def regex_extractor(self, text: str):    
        # Regex to extract possible song and artist names
        artist_regex = r"của ([^\n]+)(?:\s+(?:đi|nha|em))?"
        extracted_artist = None

        # Extract the artist name
        artist_match = re.search(artist_regex, text, re.IGNORECASE)
        if artist_match:
            extracted_artist = artist_match.group(1).strip()

        return extracted_artist


class ActionPlayGenrePlaylist(Action):
    def name(self) -> Text:
        return "action_play_genre"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:      
        genre = tracker.get_slot('genre')
        print(genre)
        found_genre = self.match_with_knowledge_base(genre)
        
        if not found_genre:
            found_genre = self.verify_with_spotify(genre)
            # Update knowledge base if matches found from Spotify
            if found_genre:
                self.update_knowledge_base("genres", found_genre)
        
        # Step 2: Perform the final action based on found matches
        if found_genre:
            # Play song using Spotify API
            if self.search_on_spotify(found_genre):
                response_text = f"Đang phát dòng nhạc {found_genre}."
                dispatcher.utter_message(text=response_text)
            else:
                dispatcher.utter_message(response="utter_default_fallback")
        else:
            # Step 3: Fallback using regex extraction
            regex_extracted_genre = self.regex_extractor(tracker.latest_message.get("text"))
            if regex_extracted_genre:
                found_genre = regex_extracted_genre
                self.search_on_spotify( found_genre)
                dispatcher.utter_message(text=f"Đang phát dòng nhạc {found_genre}.")
            else:
                dispatcher.utter_message(text="Xin lỗi, em không thể tìm được dòng nhạc này, xin hãy thử lại.")

        return [AllSlotsReset()]
    def match_with_knowledge_base(self, genre: str):
        found_genre = None

        # Check artist against knowledge base with WER
        if genre:
            for known_genre in knowledge_base["genres"]:
                if word_error_rate(known_genre.lower(), genre.lower()) < 0.2:
                    found_genre = known_genre
                    break

        return found_genre

    def verify_with_spotify(self, genre: str):
        found_genre = None

        # Search Spotify for the artist
        if genre:
            genre_result = sp.search(q=f"{genre}", type='playlist', limit=1)
            if genre_result['playlists']['items']:
                found_genre = found_genre['playlists']['items'][0]['name'].lower()

        return found_genre

    def update_knowledge_base(self, category: str, new_entry: str):
        if new_entry not in knowledge_base[category]:
            knowledge_base[category].append(new_entry)

            # Save updated knowledge base to the JSON file
            with open(knowledge_base_filename, 'w', encoding='utf-8') as kb_file:
                json.dump(knowledge_base, kb_file, ensure_ascii=False, indent=4)

    def search_on_spotify(self, genre: str = None):
        print(genre)
        result = sp.search(q=f"{genre}", type='playlist', limit=1)
        if result['playlists']['items']:
            track_uri = result['playlists']['items'][0]['uri']
            # Play the track
            sp.start_playback(context_uri=track_uri)
            return True
        return False

    def regex_extractor(self, text: str):    
        # Regex to extract possible song and artist names
        genre_regex = r"nhạc ([^\n]+)(?:\s+(?:đi|nha|em))?"
        extracted_genre = None

        # Extract the artist name
        genre_match = re.search(genre_regex, text, re.IGNORECASE)
        if genre_match:
            extracted_genre = genre_match.group(1).strip()

        return extracted_genre
    

class ActionPlaySong(Action):

    def name(self) -> Text:
        return "action_play_song"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: DomainDict) -> list:
        # Extract slots
        song = tracker.get_slot("song")

        found_song = self.match_with_knowledge_base(song)
        response_text = ""

        # Step 1: If no match found in knowledge base, try verifying with Spotify
        if not found_song:
            found_song = self.verify_with_spotify(song)
            # Update knowledge base if matches found from Spotify
            if found_song:
                self.update_knowledge_base("songs", found_song)

        # Step 2: Perform the final action based on found matches
        if found_song:
            # Play song using Spotify API
            if self.search_on_spotify(found_song):
                response_text = f"Đang phát bài '{found_song}'"
                dispatcher.utter_message(text=response_text)
            else:
                dispatcher.utter_message(template="utter_default_fallback")
        else:
            # Step 3: Fallback using regex extraction
            regex_extracted_song = self.regex_extractor(tracker.latest_message.get("text"))
            if regex_extracted_song:
                response_text += f"Đang phát bài '{regex_extracted_song}'"
                found_song = regex_extracted_song
                self.search_on_spotify(found_song)
                dispatcher.utter_message(text=response_text)
            else:
                dispatcher.utter_message(text="Xin lỗi, em không thể tìm được bài hát này, xin hãy thử lại.")

        return []

    def match_with_knowledge_base(self, song: str):
        found_song = None

        # Check song against knowledge base with WER
        if song:
            for known_song in knowledge_base["songs"]:
                if word_error_rate(known_song.lower(), song.lower()) < 0.2:
                    found_song = known_song
                    break
        return found_song

    def verify_with_spotify(self, song: str):
        found_song = None

        # Search Spotify for the song
        if song:
            song_result = sp.search(q=f"track:{song}", type='track', limit=1)
            if song_result['tracks']['items']:
                found_song = song_result['tracks']['items'][0]['name'].lower()

        return found_song

    def update_knowledge_base(self, category: str, new_entry: str):
        if new_entry not in knowledge_base[category]:
            knowledge_base[category].append(new_entry)

            # Save updated knowledge base to the JSON file
            with open(knowledge_base_filename, 'w', encoding='utf-8') as kb_file:
                json.dump(knowledge_base, kb_file, ensure_ascii=False, indent=4)

    def search_on_spotify(self, song: str):
        query = f"track:{song}"

        result = sp.search(q=query, type='track', limit=1)
        if result['tracks']['items']:
            track_uri = result['tracks']['items'][0]['uri']
            # Play the track
            sp.start_playback(uris=[track_uri])
            return True
        return False

    def regex_extractor(self, text: str):
        # Regex to extract possible song and artist names
        song_regex = r"bài ([^\n]+)"

        extracted_song = None

        # Extract the song name
        song_match = re.search(song_regex, text, re.IGNORECASE)
        if song_match:
            extracted_song = song_match.group(1).strip()

        return extracted_song


class ActionDefaultFallback(Action):
    """Custom fallback action"""

    def name(self) -> Text:
        return "action_default_fallback"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[EventType]:

        # Log the fallback event if necessary
        user_message = tracker.latest_message.get('text')
        print(f"Fallback triggered. User said: {user_message}")

        # Optionally, track the number of fallback attempts
        fallback_count = tracker.get_slot('fallback_count') or 0
        fallback_count += 1

        # Limit the number of fallback attempts
        if fallback_count < 3:
            dispatcher.utter_message(response="utter_default_fallback")
            return [SlotSet("fallback_count", fallback_count)]
        else:
            dispatcher.utter_message(text="I'm sorry, I still couldn't understand. Let's try something else.")
            return [SlotSet("fallback_count", 0), AllSlotsReset()]


class ActionQueryWeather(Action):
    def name(self) -> str:
        return "action_query_weather"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: dict) -> list:

        # Extract the location and date from the user message
        location = tracker.get_slot("location")
        date = tracker.get_slot("date") if tracker.get_slot("date") else 'hiện tại'
        clarify_district = tracker.get_slot("clarify_district")
        specific_date = tracker.get_slot("specific_date")
        
        if location is None:
            current_location = geocoder.ip('me')
            if current_location.ok:
                closest_location, distance = self.find_closest_location(current_location.latlng[0], current_location.latlng[1])
                if distance < 10:
                    specific_date = self.convert_to_specific_date(date)
                    return self.query_weather_by_geo(closest_location, closest_location['name'], specific_date, dispatcher)
            else:
                dispatcher.utter_message(text="Không thể lấy vị trí hiện tại của bạn.")
                return []
        
        if not specific_date:
            specific_date = self.convert_to_specific_date(date)
        
        if clarify_district and location:
            # We are in the follow-up step where user clarified the province
            return self.handle_clarification(dispatcher, clarify_district, specific_date, location)

        # Access 'geo' data from the knowledge base
        provinces = knowledge_base['geo'].get('province', [])
        districts = knowledge_base['geo'].get('district', [])

        # Look for the location in provinces
        matched_provinces = [p for p in provinces if p['name'].lower() == location.lower()]
        matched_districts = [d for d in districts if d['name'].lower() == location.lower()]

        # If the location is found in provinces
        if  matched_provinces:
            return self.query_weather_by_geo(matched_provinces[0], matched_provinces[0]['name'], specific_date, dispatcher)

        # If the location is found in districts, check for duplicates
        if matched_districts:
            if len(matched_districts) > 1:
                # Ask user to clarify the province if multiple districts with the same name exist
                province_options = [d['province'] for d in matched_districts]
                for option in province_options:
                    options_text = ' hay '.join(option)
                dispatcher.utter_message(text=f"Mình muốn xem thời tiết ở {options_text} ạ?")
                return [SlotSet("clarify_district", matched_districts[0]), SlotSet("specific_date", specific_date)]
            else:
                province = matched_districts[0]['province']
                return self.query_weather_by_geo(matched_districts[0], f"{matched_districts[0]['name']}, {province}", specific_date, dispatcher)

        # If no matches were found
        dispatcher.utter_message(text=f"Sorry, I couldn't find {location} in my knowledge base.")
        return [AllSlotsReset()]
    
    def handle_clarification(self, dispatcher, district_name, date, province_name):
        """Handle the user's follow-up response by combining the district and province."""

        # Search for the correct district-province pair
        matched_district = next(
            (d for d in knowledge_base['geo']['district'] if d['name'].lower() == district_name.lower() and d['province'].lower() == province_name.lower()),
            None
        )

        if matched_district:
            location_name = f"{district_name}, {province_name}"
            return self.query_weather_by_geo(matched_district, location_name, date, dispatcher)
        else:
            dispatcher.utter_message(text=f"Sorry, I couldn't find {district_name} in {province_name}.")
            return []
        
    def convert_to_specific_date(self, date_str):
        """
        Convert vague dates (e.g., 'ngày mai') into specific dates.
        Handle additional cases such as 'end of the week', 'start of the month', 'only day', etc.
        """
        today = datetime.now()

        # Handle vague dates
        if date_str in ["hôm nay", "bây giờ", "hiện tại"]:
            
            return today.strftime("%Y-%m-%d")
        elif date_str == "ngày mai":
            return (today + timedelta(days=1)).strftime("%Y-%m-%d")
        elif date_str in ["ngày kia", "ngày mốt"]:
            return (today + timedelta(days=2)).strftime("%Y-%m-%d")
        elif date_str in ["cuối tuần"]:
            # Get the next Sunday
            return (today + timedelta(days=(6 - today.weekday()))).strftime("%Y-%m-%d")
        elif date_str in ["đầu tuần"]:
            # Get the next Monday
            return (today - timedelta(days=today.weekday())).strftime("%Y-%m-%d")
        elif date_str in ["cuối tháng"]:
            # Get the last day of the current month
            last_day = calendar.monthrange(today.year, today.month)[1]
            return today.replace(day=last_day).strftime("%Y-%m-%d")
        elif date_str in ["đầu tháng"]:
            # Return the first day of the current month
            return today.replace(day=1).strftime("%Y-%m-%d")

        # Handle when only a day is provided, assume the current month
        day_only_pattern = r"ngày (\d{1,2})"
        match_day_only = re.search(day_only_pattern, date_str)

        if match_day_only:
            day = int(match_day_only.group(1))
            try:
                specific_date = today.replace(day=day)
                if specific_date < today:
                    # If the date is in the past, assume next month
                    specific_date = (specific_date + timedelta(days=calendar.monthrange(today.year, today.month)[1]))
                return specific_date.strftime("%Y-%m-%d")
            except ValueError:
                return today.strftime("%Y-%m-%d")

        # Try to match specific date patterns like 'ngày 20 tháng 6'
        specific_date_pattern = r"ngày (\d{1,2}) tháng (\d{1,2})"
        match = re.search(specific_date_pattern, date_str)

        if match:
            day = int(match.group(1))
            month = int(match.group(2))

            # Construct the full date (assuming the current year)
            specific_date = datetime(today.year, month, day)

            return specific_date.strftime("%Y-%m-%d")

        # If no date could be identified, return None
        return today.strftime("%Y-%m-%d") 


    def query_weather_by_geo(self, location, location_name, date, dispatcher):
        """
        Query the weather API based on the provided date. If the date is today, query the current weather.
        Otherwise, query the forecast API for future weather.
        """
        # Your OpenWeatherMap API key
        api_key = "7fd54ba58d8d7bb0736a5770b52616e5"  # Replace with your API key
        
        # Determine if the date is today or in the future
        today = datetime.now().strftime("%Y-%m-%d")
        
        if date == today:
            # Call current weather API for today's weather
            base_url = "http://api.openweathermap.org/data/2.5/weather"
            params = {
                "lat": location['latitude'],
                "lon": location['longitude'],
                "appid": api_key,
                "units": "metric",  # Use metric units for temperature in Celsius
                "lang": "vi"
            }
            return self.query_current_weather(base_url, params, location_name, dispatcher)
        elif date > today:
            # Call forecast API for future weather
            base_url = "http://api.openweathermap.org/data/2.5/forecast"
            params = {
                "lat": location['latitude'],
                "lon": location['longitude'],
                "appid": api_key,
                "units": "metric",  # Use metric units for temperature in Celsius
                "cnt": 16,  # Forecast for multiple timestamps (e.g., 5-day forecast every 3 hours)
                "lang": "vi"
            }
            return self.query_forecast_weather(base_url, params, location_name, date, dispatcher)
        else:
            dispatcher.utter_message(text="Có vấn đề với ngày của bạn, hãy thử lại sau")

    def query_current_weather(self, base_url, params, location_name, dispatcher):
        """
        Query the current weather API and return the result.
        """
        try:
            response = requests.get(base_url, params=params)
            data = response.json()

            if response.status_code == 200:
                current = datetime.now()
                # Parse the weather data
                weather_description = data["weather"][0]["description"] if data["weather"][0]["id"] != 800 else data["weather"][0]["description"]
                temperature = data["main"]["temp"]
                temp_feel = data["main"]["feels_like"]
                humidity = data ["main"]["humidity"]
                response_text = (
                    f"Thời tiết lúc {current.hour} giờ {current.minute} tại {location_name} có {weather_description}" 
                    f" với nhiệt độ {temperature} độ, cảm giác như {temp_feel} độ."
                    f" Độ ẩm hiện tại là {humidity} phần trăm."
                )

                # Create a response message
                dispatcher.utter_message(text=response_text)
            else:
                dispatcher.utter_message(text=f"Sorry, I couldn't find the current weather information for {location_name}.")

        except Exception as e:
            dispatcher.utter_message(text="Sorry, there was an error fetching the current weather information.")

        return [AllSlotsReset()]

    def query_forecast_weather(self, base_url, params, location_name, target_date, dispatcher):
        """
        Query the forecast API for future weather and return the result.
        """
        try:
            response = requests.get(base_url, params=params)
            data = response.json()

            if response.status_code == 200:
                forecast_list = data.get("list", [])
                forecast_for_date = None

                # Search for the forecast closest to the target date (e.g., closest time in 5-day forecast)
                for forecast in forecast_list:
                    forecast_date, forecast_time = forecast["dt_txt"].split()   
                    # Check if the date matches the target date and the time is 12:00:00 (noon)
                    if forecast_date == target_date and forecast_time == "12:00:00":
                        forecast_for_date = forecast
                        break

                if forecast_for_date:
                    weather_description = forecast_for_date["weather"][0]["description"] if forecast_for_date["weather"][0]["id"] != 800 else forecast_for_date["weather"][0]["description"] + ", nắng đẹp"
                    temperature = forecast_for_date["main"]["temp"]
                    temp_feel = forecast_for_date["main"]["feels_like"]
                    humidity = forecast_for_date ["main"]["humidity"]
                    day = target_date.split("-")[2]
                    month = target_date.split("-")[1]
                    response_text = (
                        f"Dự báo thời tiết ngày {day} tháng {month} tại {location_name} có {weather_description}" 
                        f" với nhiệt độ {temperature} độ, cảm giác như {temp_feel} độ."
                        f" Độ ẩm dự đoán là {humidity} phần trăm."
                    )

                    # Create a response message
                    dispatcher.utter_message(text=response_text)
                else:
                    dispatcher.utter_message(text=f"Sorry, I couldn't find the forecast for {target_date} in {location_name}.")
            else:
                dispatcher.utter_message(text=f"Sorry, I couldn't retrieve the weather forecast for {location_name}.")

        except Exception as e:
            dispatcher.utter_message(text=f"Sorry, there was an error fetching the weather forecast information.")

        return [AllSlotsReset()]
    
    def find_closest_location(self, user_lat, user_lon):
        closest_district = None
        min_distance = float("inf")

        # Search through districts
        for district in knowledge_base['geo']['district']:
            district_lat = district['latitude']
            district_lon = district['longitude']
            distance = self.haversine(user_lat, user_lon, district_lat, district_lon)

            if distance < min_distance:
                min_distance = distance
                closest_district = district

        return closest_district, min_distance

    def haversine(self, lat1, lon1, lat2, lon2):
        """
        Calculate the Haversine distance between two points on the Earth (specified in decimal degrees).
        Returns the distance in kilometers.
        """
        # Convert latitude and longitude from degrees to radians
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])

        # Haversine formula
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))
        r = 6371  # Radius of Earth in kilometers. Use 3956 for miles.
        return r * c




# This files contains your custom actions which can be used to run
# custom Python code.
#
# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/custom-actions


# This is a simple example for a custom action which utters "Hello World!"

# from typing import Any, Text, Dict, List
#
# from rasa_sdk import Action, Tracker
# from rasa_sdk.executor import CollectingDispatcher
#
#
# class ActionHelloWorld(Action):
#
#     def name(self) -> Text:
#         return "action_hello_world"
#
#     def run(self, dispatcher: CollectingDispatcher,
#             tracker: Tracker,
#             domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
#
#         dispatcher.utter_message(text="Hello World!")
#
#         return []
