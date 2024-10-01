from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker, FormValidationAction
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet, EventType, AllSlotsReset
from rasa_sdk.forms import FormValidationAction
from rasa_sdk.types import DomainDict
from rasa_sdk.events import UserUtteranceReverted

# Example using Spotify's API
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import os

# Initialize Spotify client
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id='fcb535d7568e400ebad08091fbee0027',
    client_secret='c2dedace15e34e87b1af6ffd2bdd051b',
    redirect_uri='http://localhost:5000/callback',
    scope='user-modify-playback-state,user-read-playback-state'))

class ActionEndConversation(Action):
    def name(self) -> Text:
        return "action_end_conversation"

    def run(self, dispatcher, tracker, domain):
        dispatcher.utter_message(template="utter_end")
        return [UserUtteranceReverted()]

# class ValidatePlaySongForm(FormValidationAction):
#     def name(self) -> Text:
#         return "validate_play_song_form"

    # async def required_slots(
    #     self,
    #     slots_mapped_in_domain: List[Text],
    #     dispatcher: CollectingDispatcher,
    #     tracker: Tracker,
    #     domain: DomainDict,
    # ) -> List[Text]:
    #     # Dynamically define required slots based on available information
    #     required = ["song"]
    #     song = tracker.get_slot("song")
    #     if not song:
    #         required = ["song"]
    #     else:
    #         # If song is provided but artist is not, ask for artist
    #         artist = tracker.get_slot("artist")
    #         if not artist:
    #             required = ["artist"]
    #     return required

    # def validate_song(
    #     self,
    #     value: Text,
    #     dispatcher: CollectingDispatcher,
    #     tracker: Tracker,
    #     domain: DomainDict,
    # ) -> Dict[Text, Any]:
    #     # validation for the song
    #     if value:  # If 'value' is not empty
    #         print(value)
    #         return {"song": value}  # Return the valid song value
    #     else:  # If 'value' is empty
    #         return {"song": None}  # Return None for the 'song' slot
        
    # def validate_artist(
    #     self,
    #     value: Text,
    #     dispatcher: CollectingDispatcher,
    #     tracker: Tracker,
    #     domain: DomainDict,
    # ) -> Dict[Text, Any]:
    #     # validation for the artist
    #     if value:
    #         print(value)
    #         return {"artist": value}
    #     else:
    #         return {"artist": None}

    # def validate_genre(
    #     self,
    #     value: Text,
    #     dispatcher: CollectingDispatcher,
    #     tracker: Tracker,
    #     domain: DomainDict,
    # ) -> Dict[Text, Any]:
    #     # validation for the genre
    #     if value:
    #         return {"genre": value}
    #     else:
    #         return {"genre": None}

class ActionPlayTopSong(Action):

    def name(self) -> Text:
        return "action_play_top_song"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        # Get the current top 50 playlist on Spotify (using the Global Top 50 playlist)
        top_playlist_result = sp.search(q='Top 50 - Global', type='playlist', limit=1)
        if top_playlist_result['playlists']['items']:
            playlist_uri = top_playlist_result['playlists']['items'][0]['uri']
            
            # Play the top 50 playlist
            sp.start_playback(context_uri=playlist_uri)
            dispatcher.utter_message(template="utter_turn_on_music")
        else:
            dispatcher.utter_message(template="utter_default_fallback")

        return [AllSlotsReset()]

class ActionPlayArtistPlaylist(Action):

    def name(self) -> Text:
        return "action_play_artist"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:      
        artist = tracker.get_slot('artist')

        # Get the current top 50 playlist on Spotify (using the Global Top 50 playlist)
        artist_playlist_result = sp.search(q=f"artist:{artist}", type='playlist', limit=1)
        if artist_playlist_result['playlists']['items']:
            playlist_uri = artist_playlist_result['playlists']['items'][0]['uri']
            
            # Play the top 50 playlist
            sp.start_playback(context_uri=playlist_uri)
            dispatcher.utter_message(template="utter_provide_artist")
        else:
            dispatcher.utter_message(template="utter_default_fallback")

        return [AllSlotsReset()]
    
class ActionPlayGenrePlaylist(Action):

    def name(self) -> Text:
        return "action_play_genre"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:      
        genre = tracker.get_slot('genre')

        if genre:
            # Search for a playlist matching the genre
            result = sp.search(q=f"genre:{genre}", type='playlist', limit=1)
            if result['playlists']['items']:
                playlist_uri = result['playlists']['items'][0]['uri']
                # Play the playlist
                sp.start_playback(context_uri=playlist_uri)
                dispatcher.utter_message(template="utter_provide_genre")
            else:
                dispatcher.utter_message(text="Xin lỗi em không thể tìm thấy dòng nhạc đó")
        else:
            dispatcher.utter_message(template="utter_default_fallback")

        return [AllSlotsReset()]

class ActionPlaySong(Action):

    def name(self) -> Text:
        return "action_play_song"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        song = tracker.get_slot('song')

        if song:
         
            # Search for the track
            result = sp.search(q=f"track:{song}", type='track', limit=1)
            if result['tracks']['items']:
                track_uri = result['tracks']['items'][0]['uri']
                # Play the track
                sp.start_playback(uris=[track_uri])
                dispatcher.utter_message(template="utter_provide_song")
            else:
                dispatcher.utter_message(text="Xin lỗi em không thể tìm thấy bài đó")
        else:
            dispatcher.utter_message(template="utter_default_fallback")

        return [AllSlotsReset()]

class ActionPlaySongWithArtist(Action):

    def name(self) -> Text:
        return "action_play_song_with_artist"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        song = tracker.get_slot('song')
        artist = tracker.get_slot('artist')
        print(song, artist)
        

        if song and artist:
         
            # Search for the track
            result = sp.search(q=f"track:{song} artist:{artist}", type='track', limit=1)
            if result['tracks']['items']:
                track_uri = result['tracks']['items'][0]['uri']
                # Play the track
                sp.start_playback(uris=[track_uri])
                dispatcher.utter_message(template="utter_provide_song_with_artist")
            else:
                dispatcher.utter_message(text="Xin lỗi em không thể tìm thấy bài đó")
        else:
            dispatcher.utter_message(template="utter_default_fallback")

        return [AllSlotsReset()]

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
