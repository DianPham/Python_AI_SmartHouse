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
from apscheduler.schedulers.background import BackgroundScheduler
from dateutil import relativedelta
import time

# Example using Spotify's API
import spotipy
from spotipy.oauth2 import SpotifyOAuth

import os

# Initialize Spotify client
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id='fcb535d7568e400ebad08091fbee0027',
    client_secret='8128f7d68e50457fac477fb40253ae66',
    redirect_uri='http://localhost:5000/callback',
    scope='user-modify-playback-state,user-read-playback-state'))

api_key_ipstack = "91a4beec0e772afcc8f41029504fcd44"
api_key_openweather = "7fd54ba58d8d7bb0736a5770b52616e5"

# Get the directory of the current script
current_dir = os.path.dirname(os.path.abspath(__file__))

# Get the parent directory
parent_dir = os.path.abspath(os.path.join(current_dir, os.pardir))

# Construct the path to the knowledge base file in the parent directory
knowledge_base_filename = os.path.join(parent_dir, "knowledge_base.json")

with open(knowledge_base_filename, encoding="utf-8") as kb_file:
    knowledge_base = json.load(kb_file)
    
# Global scheduler instance
scheduler = BackgroundScheduler()
scheduler.start()

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


class ActionQueryWeather(Action):
    def name(self) -> str:
        return "action_query_weather"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: dict) -> list:

        # Extract the location and date from the user message
        time = tracker.get_slot("time")
        date = tracker.get_slot("date") if tracker.get_slot("date") else 'hiện tại'
        sub_time = tracker.get_slot("sub_time")
        sub_date = tracker.get_slot("sub_date")
        location = tracker.get_slot("location")  
        clarify_district = tracker.get_slot("clarify_district")
        specific_date = tracker.get_slot("specific_date")
        
        if location is None:
            response = requests.get(f"http://api.ipstack.com/check?access_key={api_key_ipstack}")

            if response.status_code == 200:
                data = response.json()
                latitude = data.get('latitude')
                longitude = data.get('longitude')
                if latitude and longitude:
                    closest_location, distance = self.find_closest_location(latitude, longitude)
                    if distance < 10:
                        specific_date = self.build_datetime(time, sub_time, date, sub_date)
                        print(specific_date)
                        return self.query_weather_by_geo(closest_location, closest_location['name'], specific_date, dispatcher)
            else:
                dispatcher.utter_message(text="Không thể lấy vị trí hiện tại của anh.")
                return [AllSlotsReset()]
        
        if not specific_date:
            specific_date = self.build_datetime(time, sub_time, date, sub_date)
        
        specific_date = str(specific_date)
        
        if clarify_district and location:
            # We are in the follow-up step where user clarified the province
            return self.handle_clarification(dispatcher, clarify_district, specific_date, location)

        # Access 'geo' data from the knowledge base
        provinces = knowledge_base['geo'].get('province', [])
        districts = knowledge_base['geo'].get('district', [])

        # Look for the location in provinces
        matched_provinces = [p for p in provinces if p['name'].lower() == location.lower().strip()]
        matched_districts = [d for d in districts if d['name'].lower() == location.lower().strip()]

        # If the location is found in provinces
        if  matched_provinces:
            return self.query_weather_by_geo(matched_provinces[0], matched_provinces[0]['name'], specific_date, dispatcher)

        # If the location is found in districts, check for duplicates
        if matched_districts:
            if len(matched_districts) > 1:
                # Ask user to clarify the province if multiple districts with the same name exist
                province_options = [d['province'] for d in matched_districts]
                print(province_options)
                for option in province_options[:-1]:
                    options_text = option + ' hay '
                options_text = options_text + province_options[-1]
                print(options_text)
                dispatcher.utter_message(text=f"Mình muốn xem thời tiết ở {options_text} ạ")
                print(matched_districts[0]['name'])
                return [SlotSet("clarify_district", matched_districts[0]['name']), SlotSet("specific_date", specific_date)]
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
        return [AllSlotsReset()]

    def build_datetime(self, time_str, sub_time, date_str, sub_date):
        specific_date = self.convert_to_specific_date(date_str, sub_date)
        specific_time = self.convert_to_specific_time(time_str, sub_time)
        return datetime.strptime(str(specific_date) + " " + str(specific_time), '%Y-%m-%d %H:%M:%S')
        
    
    def convert_to_specific_date(self, date_str, sub_date):
        """
        Convert relative date expressions like 'ngày mai', 'thứ hai tuần sau', 'thứ ba cuối tháng' into specific dates.
        """
        today = datetime.now()

        # Default date to today if no date or sub_date is given
        if not date_str and not sub_date:
            return today.strftime("%Y-%m-%d")

        # Map Vietnamese weekdays to Python weekday numbers (Monday = 0, Sunday = 6)
        weekday_map = {
            "thứ 2": 0,
            "thứ 3": 1,
            "thứ 4": 2,
            "thứ 5": 3,
            "thứ 6": 4,
            "thứ 7": 5,
            "chủ nhật": 6
        }

        # Check if date_str is a specific weekday like "thứ hai", "thứ ba", etc.
        if date_str in weekday_map:
            target_weekday = weekday_map[date_str]
            current_weekday = today.weekday()

            # Calculate how many days to add to get to the target weekday
            if sub_date == "tuần sau":
                # Move to the same weekday in the next week
                days_ahead = (target_weekday - current_weekday + 7) % 7 + 7
            elif sub_date == "tháng sau":
                # Move to the same weekday in the next month
                next_month = today + relativedelta.relativedelta(months=1)
                days_ahead = (target_weekday - next_month.weekday()) % 7
                specific_date = next_month + timedelta(days=days_ahead)
                return specific_date.strftime("%Y-%m-%d")
            else:
                # Default case: Move to the same weekday in the current or upcoming week
                days_ahead = (target_weekday - current_weekday + 7) % 7
            specific_date = today + timedelta(days=days_ahead)
            return specific_date.strftime("%Y-%m-%d")
        else:
            if date_str in ["hôm nay", "bây giờ", "hiện tại", "nay"]:
                return today.strftime("%Y-%m-%d")
            elif date_str in ["ngày mai", "mai"]:
                return (today + timedelta(days=1)).strftime("%Y-%m-%d")
            elif date_str in ["ngày kia", "ngày mốt"]:
                return (today + timedelta(days=2)).strftime("%Y-%m-%d")
        # Handle sub_date modifiers for relative expressions
        if sub_date == "cuối tuần":
            # Get the next Sunday
            next_sunday = today + timedelta(days=(6 - today.weekday()))
            return next_sunday.strftime("%Y-%m-%d")
        elif sub_date == "cuối tháng":
            # Get the last day of the current month
            last_day = calendar.monthrange(today.year, today.month)[1]
            return today.replace(day=last_day).strftime("%Y-%m-%d")
        elif sub_date == "đầu tuần":
            # Get the upcoming Monday
            next_monday = today + timedelta(days=(7 - today.weekday()) % 7)
            return next_monday.strftime("%Y-%m-%d")
        elif sub_date == "đầu tháng":
            # Get the first day of the next month
            nextmonth = today + relativedelta.relativedelta(months=1)
            return nextmonth.replace(day=1).strftime("%Y-%m-%d")
        elif sub_date == "tuần sau":
            return (today + timedelta(days=7)).strftime("%Y-%m-%d")
        elif sub_date == "tháng sau":
            next_month = today + relativedelta.relativedelta(months=1)
            return next_month.replace(day=1).strftime("%Y-%m-%d")

        # Try to match specific date patterns like 'ngày 20 tháng 6'
        specific_date_pattern = r"ngày (\d{1,2}) tháng (\d{1,2})"
        match = re.search(specific_date_pattern, date_str)

        if match:
            day = int(match.group(1))
            month = int(match.group(2))

            # Construct the full date (assuming the current year)
            specific_date = datetime(today.year, month, day)
            return specific_date.strftime("%Y-%m-%d")

        # Default to today if no relative date is given
        return today.strftime("%Y-%m-%d")

    def convert_to_specific_time(self, time_str, sub_time):
        """
        Parse the time and date strings into a datetime object.
        Handle cases like "7 giờ 30", "8 giờ rưỡi", "7 giờ tối", "5 giờ 30 sáng", etc.
        """
        print(f"time_str: {time_str}, sub_time: {sub_time}")
        try:
            # Return if no time information given
            if not time_str and not sub_time:
                return datetime.now().strftime("%H:%M:%S")

            specific_time = datetime.now()
            time_format = "%H giờ %M"
            
            # Case 1: Both time and sub_time are provided
            if time_str:
                
                # Preprocess time string
                if "rưỡi" in time_str:
                    time_str = time_str.replace("rưỡi", "").strip() + " giờ 30"
                elif time_str.endswith("phút"):
                    time_str = time_str.replace("phút", "").strip()
                elif time_str.split()[-1] == "giờ":
                    time_str = time_str + " 00"
                    
                print("Handling both time and sub_time!")
                try:
                    specific_time = datetime.strptime(time_str, time_format)
                except ValueError:
                    print("Error parsing time_str. Returning current time.")
                    return datetime.now().strftime("%H:%M:%S")
                
                # Adjust for afternoon/evening if sub_time suggests it
                if sub_time in ["chiều", "buổi chiều", "tối", "buổi tối"]:
                    if specific_time.hour < 12:  # Ensure it's PM
                        specific_time += timedelta(hours=12)
            
            # Case 2: Only sub_time is provided
            else:
                print("Handling only sub_time!")
                if sub_time in ["sáng", "buổi sáng"]:
                    specific_time = datetime.strptime("07 giờ 00", time_format)
                elif sub_time in ["trưa", "buổi trưa"]:
                    specific_time = datetime.strptime("12 giờ 00", time_format)
                elif sub_time in ["chiều", "buổi chiều"]:
                    specific_time = datetime.strptime("14 giờ 00", time_format)
                elif sub_time in ["tối", "buổi tối"]:
                    specific_time = datetime.strptime("19 giờ 00", time_format)
                    
            print(specific_time.strftime("%H:%M:%S"))
            return specific_time.strftime("%H:%M:%S")

        except Exception as e:
            print(e)
            return None

    def query_weather_by_geo(self, location, location_name, date, dispatcher):
        """
        Query the weather API based on the provided date. If the date is today, query the current weather.
        Otherwise, query the forecast API for future weather.
        """

        try:
            date = datetime.strptime(date, "%Y-%m-%d %H:%M:%S")  # Example: Convert from string to datetime
        except ValueError:
            dispatcher.utter_message(text="Ngày không hợp lệ, hãy thử lại sau")
            return [AllSlotsReset()]
        
        today = datetime.now()
        
        if date.strftime("%Y-%m-%d") == today.strftime("%Y-%m-%d") and date.strftime("%H") == today.strftime("%H"):
            # Call current weather API for today's weather
            base_url = "http://api.openweathermap.org/data/2.5/weather"
            params = {
                "lat": location['latitude'],
                "lon": location['longitude'],
                "appid": api_key_openweather,
                "units": "metric",  # Use metric units for temperature in Celsius
                "lang": "vi"
            }
            return self.query_current_weather(base_url, params, location_name, dispatcher)
        elif date.strftime("%Y-%m-%d") > today.strftime("%Y-%m-%d"):
            # Call forecast API for future weather
            base_url = "http://api.openweathermap.org/data/2.5/forecast"
            params = {
                "lat": location['latitude'],
                "lon": location['longitude'],
                "appid": api_key_openweather,
                "units": "metric",  # Use metric units for temperature in Celsius
                "cnt": 16,  # Forecast for multiple timestamps (e.g., 5-day forecast every 3 hours)
                "lang": "vi"
            }
            return self.query_forecast_weather(base_url, params, location_name, date, dispatcher)
        else:
            dispatcher.utter_message(text="Có vấn đề với ngày của anh, hãy thử lại sau")
            return [AllSlotsReset()]

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
            return [AllSlotsReset()]

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
                forecast_for_date = self.get_closest_forecast(forecast_list, target_date)               
                

                if forecast_for_date:
                    weather_description = forecast_for_date["weather"][0]["description"] if forecast_for_date["weather"][0]["id"] != 800 else forecast_for_date["weather"][0]["description"] + ", nắng đẹp"
                    temperature = forecast_for_date["main"]["temp"]
                    temp_feel = forecast_for_date["main"]["feels_like"]
                    humidity = forecast_for_date ["main"]["humidity"]
                    day = target_date.strftime("%d")
                    month = target_date.strftime("%m")
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
            return [AllSlotsReset()]

        except Exception as e:
            print(e)
            dispatcher.utter_message(text=f"Sorry, there was an error fetching the weather forecast information.")
            return [AllSlotsReset()]
    
    def get_closest_forecast(self, forecast_list, target_time):
        """
        Given a list of forecast times and the target time, find the closest forecast time.
        """
        closest_forecast = None
        min_diff = timedelta.max  # Initialize with the maximum possible difference

        for forecast in forecast_list:
            # Extract the forecast time from the OpenWeather data (forecast['dt_txt'])
            forecast_time = datetime.strptime(forecast['dt_txt'], '%Y-%m-%d %H:%M:%S')

            # Calculate the time difference between forecast time and user requested time
            time_diff = abs(forecast_time - target_time)

            # If this forecast is closer to the requested time, update the closest_forecast
            if time_diff < min_diff:
                min_diff = time_diff
                closest_forecast = forecast

        return closest_forecast
    
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

class ActionCreateReminder(Action):
    def name(self) -> str:
        return "action_create_reminder"

    def run(self, dispatcher, tracker, domain):
        # Extract information from slots
        time = tracker.get_slot("time")
        date = tracker.get_slot("date")
        sub_time = tracker.get_slot("sub_time")
        sub_date = tracker.get_slot("sub_date")
        event = tracker.get_slot("event")
        specific_date = tracker.get_slot("specific_date")
        specific_time = tracker.get_slot("specific_time")

        print("time: " + str(time))
        print("sub_time: " + str(sub_time))
        print("specific_date: " + str(specific_date))
        print("specific_time: " + str(specific_time))
        
        # Build the reminder time
        if not specific_time:
            specific_time = self.convert_to_specific_time(time, sub_time)
        if not specific_date:
            specific_date = self.convert_to_specific_date(date, sub_date)
        
        if specific_time and not event:
            dispatcher.utter_message(text="anh muốn đặt lời nhắc cho việc gì ạ")
            return [AllSlotsReset(),SlotSet("specific_time", specific_time), SlotSet("specific_date", specific_date)]

        # If we still don't have time or date, prompt the user for clarification
        elif not specific_time and event:
            dispatcher.utter_message(text=f"anh muốn em nhắc anh vào lúc nào")
            return [AllSlotsReset(),SlotSet("event", event), SlotSet("specific_date", specific_date)]
        
        elif specific_time and event:
            
            reminder_time = datetime.strptime(str(specific_date) + " " + str(specific_time), '%Y-%m-%d %H:%M:%S')
            # Extract and format the time and date
            formatted_time_hour = reminder_time.strftime("%H")
            formatted_time_minute = reminder_time.strftime("%M")
            formatted_date_day = reminder_time.strftime("%d")
            formatted_date_month = reminder_time.strftime("%m")
            formatted_date_year = reminder_time.strftime("%Y")

            # Schedule the reminder
            self.schedule_reminder(event, reminder_time, tracker.sender_id)

            # Confirmation message
            dispatcher.utter_message(
                text=f"Đã đặt lời nhắc{' cho ' + event if event else ''} lúc {formatted_time_hour} giờ {formatted_time_minute} phút "
                        f"ngày {formatted_date_day} tháng {formatted_date_month} năm {formatted_date_year}."
            )        
        else:
            dispatcher.utter_message(text="Xin lỗi, em không hiểu thời gian anh muốn đặt lời nhắc.")
            
        return [AllSlotsReset()]

    def schedule_reminder(self, task, reminder_time, user_id):
        """
        Schedule a reminder using APScheduler that will trigger at the specified time.
        """
        set_time = datetime.now()
        scheduler.add_job(
            func=self.play_alarm,
            trigger='date',
            run_date=reminder_time,
            args=[task, user_id, set_time],
            id=f"reminder_{user_id}_{reminder_time}",
            replace_existing=True
        )

    def play_alarm(self, task, user_id, time):
        """
        Play the alarm and send the reminder task to a specified endpoint.
        """
        endpoint_url = "http://localhost:5000/receive_reminder"
        if not task:
            formatted_time_hour = time.strftime("%H")
            formatted_time_minute = time.strftime("%M")
            formatted_date_day = time.strftime("%d")
            formatted_date_month = time.strftime("%m")
            formatted_date_year = time.strftime("%Y")
            task = f"được đặt lúc {formatted_time_hour} giờ {formatted_time_minute} phút "
            f"ngày {formatted_date_day} tháng {formatted_date_month} năm {formatted_date_year}"

        payload = {
            'user_id': user_id,
            'task': task,
            'triggered_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        try:
            response = requests.post(endpoint_url, json=payload)
            if response.status_code == 200:
                print("Reminder sent successfully!")
            else:
                print(f"Failed to send reminder. Status code: {response.status_code}")
        except Exception as e:
            print(f"Error sending reminder: {e}")

    
    def convert_to_specific_date(self, date_str, sub_date):
        """
        Convert relative date expressions like 'ngày mai', 'thứ hai tuần sau', 'thứ ba cuối tháng' into specific dates.
        """
        today = datetime.now()

        # Default date to today if no date or sub_date is given
        if not date_str and not sub_date:
            return today.strftime("%Y-%m-%d")

        # Map Vietnamese weekdays to Python weekday numbers (Monday = 0, Sunday = 6)
        weekday_map = {
            "thứ 2": 0,
            "thứ 3": 1,
            "thứ 4": 2,
            "thứ 5": 3,
            "thứ 6": 4,
            "thứ 7": 5,
            "chủ nhật": 6
        }

        # Check if date_str is a specific weekday like "thứ hai", "thứ ba", etc.
        if date_str in weekday_map:
            target_weekday = weekday_map[date_str]
            current_weekday = today.weekday()

            # Calculate how many days to add to get to the target weekday
            if sub_date == "tuần sau":
                # Move to the same weekday in the next week
                days_ahead = (target_weekday - current_weekday + 7) % 7 + 7
            elif sub_date == "tháng sau":
                # Move to the same weekday in the next month
                next_month = today + relativedelta.relativedelta(months=1)
                days_ahead = (target_weekday - next_month.weekday()) % 7
                specific_date = next_month + timedelta(days=days_ahead)
                return specific_date.strftime("%Y-%m-%d")
            else:
                # Default case: Move to the same weekday in the current or upcoming week
                days_ahead = (target_weekday - current_weekday + 7) % 7
            specific_date = today + timedelta(days=days_ahead)
            return specific_date.strftime("%Y-%m-%d")
        else:
            if date_str in ["hôm nay", "bây giờ", "hiện tại", "nay"]:
                return today.strftime("%Y-%m-%d")
            elif date_str in ["ngày mai", "mai"]:
                return (today + timedelta(days=1)).strftime("%Y-%m-%d")
            elif date_str in ["ngày kia", "ngày mốt"]:
                return (today + timedelta(days=2)).strftime("%Y-%m-%d")
        # Handle sub_date modifiers for relative expressions
        if sub_date == "cuối tuần":
            # Get the next Sunday
            next_sunday = today + timedelta(days=(6 - today.weekday()))
            return next_sunday.strftime("%Y-%m-%d")
        elif sub_date == "cuối tháng":
            # Get the last day of the current month
            last_day = calendar.monthrange(today.year, today.month)[1]
            return today.replace(day=last_day).strftime("%Y-%m-%d")
        elif sub_date == "đầu tuần":
            # Get the upcoming Monday
            next_monday = today + timedelta(days=(7 - today.weekday()) % 7)
            return next_monday.strftime("%Y-%m-%d")
        elif sub_date == "đầu tháng":
            # Get the first day of the next month
            nextmonth = today + relativedelta.relativedelta(months=1)
            return nextmonth.replace(day=1).strftime("%Y-%m-%d")
        elif sub_date == "tuần sau":
            return (today + timedelta(days=7)).strftime("%Y-%m-%d")
        elif sub_date == "tháng sau":
            next_month = today + relativedelta.relativedelta(months=1)
            return next_month.replace(day=1).strftime("%Y-%m-%d")

        # Try to match specific date patterns like 'ngày 20 tháng 6'
        specific_date_pattern = r"ngày (\d{1,2}) tháng (\d{1,2})"
        match = re.search(specific_date_pattern, date_str)

        if match:
            day = int(match.group(1))
            month = int(match.group(2))

            # Construct the full date (assuming the current year)
            specific_date = datetime(today.year, month, day)
            return specific_date.strftime("%Y-%m-%d")

        # Default to today if no relative date is given
        return today.strftime("%Y-%m-%d")

    def convert_to_specific_time(self, time_str, sub_time):
        """
        Parse the time and date strings into a datetime object.
        Handle cases like "7 giờ 30", "8 giờ rưỡi", "7 giờ tối", "5 giờ 30 sáng", etc.
        """
        try:
            # Return if no time information given
            if not time_str and not sub_time:
                return None 
            
            specific_time = datetime.now()
            time_format = "%H giờ %M"

            # Case 1: Both time and sub_time are provided
            if time_str:
                
                # Preprocess time string
                if "rưỡi" in time_str:
                    time_str = time_str.replace("rưỡi", "").strip() + " giờ 30"
                elif time_str.endswith("phút"):
                    time_str = time_str.replace("phút", "").strip()
                elif time_str.split()[-1] == "giờ":
                    time_str = time_str + " 00"
                    
                print("Handling both time and sub_time!")
                try:
                    specific_time = datetime.strptime(time_str, time_format)
                except ValueError:
                    print("Error parsing time_str. Returning current time.")
                    return datetime.now().strftime("%H:%M:%S")
                
                # Adjust for afternoon/evening if sub_time suggests it
                if sub_time in ["chiều", "buổi chiều", "tối", "buổi tối"]:
                    if specific_time.hour < 12:  # Ensure it's PM
                        specific_time += timedelta(hours=12)
            
            # Case 2: Only sub_time is provided
            else:
                print("Handling only sub_time!")
                if sub_time in ["sáng", "buổi sáng"]:
                    specific_time = datetime.strptime("07 giờ 00", time_format)
                elif sub_time in ["trưa", "buổi trưa"]:
                    specific_time = datetime.strptime("12 giờ 00", time_format)
                elif sub_time in ["chiều", "buổi chiều"]:
                    specific_time = datetime.strptime("14 giờ 00", time_format)
                elif sub_time in ["tối", "buổi tối"]:
                    specific_time = datetime.strptime("19 giờ 00", time_format)
            
            print(specific_time.strftime("%H:%M:%S"))
            return specific_time.strftime("%H:%M:%S")

        except Exception as e:
            print(e)
            return None
        
class ActionCreateTimer(Action):

    def name(self) -> str:
        return "action_create_timer"

    def run(self, dispatcher, tracker, domain):
        # Extract necessary information from slots
        event = tracker.get_slot("event")  # E.g., "gọi điện cho sếp"
        time = tracker.get_slot("time")  # E.g., "5 phút", "1 giờ", "30 giây"

        # Handle if the event or time is missing
        if not event and time:
            dispatcher.utter_message(text="Anh muốn em nhắc cho việc gì")
            return [AllSlotsReset(), SlotSet("time", time)]
        
        if not time and event:
            dispatcher.utter_message(text=f"anh muốn đặt hẹn giờ trong bao lâu để em nhắc anh {event}?")
            return [AllSlotsReset(), SlotSet("event", event)]

        # If time is available, convert it to seconds
        total_seconds = self.convert_time_to_seconds(time)

        if total_seconds is not None:
            # Schedule the timer
            dispatcher.utter_message(text=f"Đã đặt hẹn giờ {time} để nhắc anh {event}.")
            self.schedule_timer(event, total_seconds, tracker.sender_id)
        else:
            dispatcher.utter_message(text="Xin lỗi, em không hiểu khoảng thời gian anh đặt.")

        return [AllSlotsReset()]

    def convert_time_to_seconds(self, time):
        """
        Convert user-provided time (in minutes, hours, seconds) to seconds.
        Handles combined units like "1 giờ 30 phút", "1 phút 30 giây", and "3 phút 15".
        """
        total_seconds = 0
        time = time.strip().lower()

        # Initialize variables to store time components
        hours, minutes, seconds = 0, 0, 0

        try:
            # Split the time string into words
            parts = time.split()

            # Iterate over the parts of the time string
            i = 0
            while i < len(parts):
                value = int(parts[i])
                
                if i + 1 < len(parts):
                    unit = parts[i + 1]
                    
                    if "giờ" in unit:
                        hours = value
                    elif "phút" in unit:
                        minutes = value
                    elif "giây" in unit:
                        seconds = value
                    i += 2  # Move to the next value-unit pair
                else:
                    # Handle cases like "3 phút 15"
                    if "phút" in parts[i - 1]:
                        seconds = value
                    i += 1
            
            # Convert everything to seconds
            total_seconds += hours * 3600
            total_seconds += minutes * 60
            total_seconds += seconds
            
            return total_seconds
        except (ValueError, IndexError):
            return None

    def schedule_timer(self, event, total_seconds, user_id):
        """
        Schedule a timer using APScheduler that will trigger after the specified time.
        """
        # Get the current time
        now = datetime.now()

        # Add total_seconds to the current time to get the run date
        run_when = now + timedelta(seconds=total_seconds)
        
        set_time = datetime.now()
        scheduler.add_job(
            func=self.play_alarm,
            trigger='date',
            run_date= run_when,
            args=[event, user_id, set_time],
            id=f"reminder_{user_id}_{time.time()}",
            replace_existing=True
        )

    def play_alarm(self, task, user_id, time):
        """
        Play the alarm and send the reminder task to a specified endpoint.
        """
        endpoint_url = "http://localhost:5000/receive_reminder"
        if not task:
            formatted_time_hour = time.strftime("%H")
            formatted_time_minute = time.strftime("%M")
            formatted_date_day = time.strftime("%d")
            formatted_date_month = time.strftime("%m")
            formatted_date_year = time.strftime("%Y")
            task = f"được đặt lúc {formatted_time_hour} giờ {formatted_time_minute} phút "
            f"ngày {formatted_date_day} tháng {formatted_date_month} năm {formatted_date_year}"

        payload = {
            'user_id': user_id,
            'task': task,
            'triggered_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        try:
            response = requests.post(endpoint_url, json=payload)
            if response.status_code == 200:
                print("Reminder sent successfully!")
            else:
                print(f"Failed to send reminder. Status code: {response.status_code}")
        except Exception as e:
            print(f"Error sending reminder: {e}")




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

    # def convert_to_specific_date(self, date_str):
    #     """
    #     Convert vague dates (e.g., 'ngày mai') into specific dates.
    #     Handle additional cases such as 'end of the week', 'start of the month', 'only day', etc.
    #     """
    #     today = datetime.now()
    #     date_str = date_str.strip()
    #     # Handle vague dates
    #     if date_str in ["hôm nay", "bây giờ", "hiện tại"]:           
    #         return today.strftime("%Y-%m-%d")
    #     elif date_str == "ngày mai":
    #         return (today + timedelta(days=1)).strftime("%Y-%m-%d")
    #     elif date_str in ["ngày kia", "ngày mốt"]:
    #         return (today + timedelta(days=2)).strftime("%Y-%m-%d")
    #     elif date_str in ["cuối tuần"]:
    #         # Get the next Sunday
    #         return (today + timedelta(days=(6 - today.weekday()))).strftime("%Y-%m-%d")
    #     elif date_str in ["đầu tuần"]:
    #         # Get the next Monday
    #         return (today - timedelta(days=today.weekday())).strftime("%Y-%m-%d")
    #     elif date_str in ["cuối tháng"]:
    #         # Get the last day of the current month
    #         last_day = calendar.monthrange(today.year, today.month)[1]
    #         return today.replace(day=last_day).strftime("%Y-%m-%d")
    #     elif date_str in ["đầu tháng"]:
    #         # Return the first day of the current month
    #         return today.replace(day=1).strftime("%Y-%m-%d")

    #     # Handle when only a day is provided, assume the current month
    #     day_only_pattern = r"ngày (\d{1,2})"
    #     match_day_only = re.search(day_only_pattern, date_str)

    #     if match_day_only:
    #         day = int(match_day_only.group(1))
    #         try:
    #             specific_date = today.replace(day=day)
    #             if specific_date < today:
    #                 # If the date is in the past, assume next month
    #                 specific_date = (specific_date + timedelta(days=calendar.monthrange(today.year, today.month)[1]))
    #             return specific_date.strftime("%Y-%m-%d")
    #         except ValueError:
    #             return today.strftime("%Y-%m-%d")

    #     # Try to match specific date patterns like 'ngày 20 tháng 6'
    #     specific_date_pattern = r"ngày (\d{1,2}) tháng (\d{1,2})"
    #     match = re.search(specific_date_pattern, date_str)

    #     if match:
    #         day = int(match.group(1))
    #         month = int(match.group(2))

    #         # Construct the full date (assuming the current year)
    #         specific_date = datetime(today.year, month, day)

    #         return specific_date.strftime("%Y-%m-%d")

    #     # If no date could be identified, return None
    #     return today.strftime("%Y-%m-%d") 
