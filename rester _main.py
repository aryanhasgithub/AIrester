import threading
import time
import os
import uuid
import asyncio
import edge_tts
import pygame
import speech_recognition as sr
import requests
from homeassistant_api import Client
from datetime import datetime
from threading import Timer
from groq import Groq
import yt_dlp
from youtubesearchpython import VideosSearch
import pyjokes
import wikipedia
import subprocess
import webcolors
import pvporcupine
import pyaudio
import struct

# Initialize pygame mixer (used for TTS and for sound prompts)
pygame.mixer.init()

# Initialize the Groq client (for cloud completions)
client = Groq(api_key="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")

class Assistant:
    def __init__(self, home_assistant_url, access_token, groqcloud_key, weather_api_key):
        # Home Assistant API client
        self.client = Client(home_assistant_url, access_token)
        self.groqcloud_key = groqcloud_key
        self.weather_api_key = weather_api_key

        # For voice recognition
        self.recognizer = sr.Recognizer()
        self.mic = sr.Microphone()

        # TTS: Using edge_tts for streaming TTS with pygame playback.
        self.speak_thread = None
        self.ACCESS_KEY = "Lfi4nZeWg1ExLIfHrKfQXsDX7wly49L0nbcXEXp/uOGkWcClaSDT0A=="  # Replace with your actual access key
        self.KEYWORD_PATH = r"C:\Users\aryan\projects\rester\spark_en_windows_v3_0_0\spark_en_windows_v3_0_0.ppn"  # Corrected path format
        self.porcupine = pvporcupine.create(access_key=self.ACCESS_KEY, keyword_paths=[self.KEYWORD_PATH])
        self.pa = pyaudio.PyAudio()
        self.audio_stream = self.pa.open(format=pyaudio.paInt16, channels=1, rate=self.porcupine.sample_rate,
                                         input=True, frames_per_buffer=self.porcupine.frame_length)


    def speak(self, message):
        """Speak the message using edge‑tts streaming and pygame for playback."""
        self.interrupt_speech()
        print("Speaking:", message)
        
        def _speak():
            filename = f"{uuid.uuid4()}.mp3"
            try:
                # Asynchronously stream TTS audio and save to file.
                asyncio.run(self._speak_async(message, filename))
                pygame.mixer.music.load(filename)
                pygame.mixer.music.play()
                # Wait until playback finishes or is interrupted.
                while pygame.mixer.music.get_busy():
                    time.sleep(0.1)
            except Exception as e:
                print("Error during TTS playback:", e)
            finally:
                if os.path.exists(filename):
                    os.remove(filename)
                    
        self.speak_thread = threading.Thread(target=_speak)
        self.speak_thread.start()

    async def _speak_async(self, message, filename):
        communicate = edge_tts.Communicate(message, voice="en-US-AriaNeural")
        with open(filename, "wb") as f:
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    f.write(chunk["data"])

    def interrupt_speech(self):
        """Stop any ongoing TTS playback."""
        try:
            pygame.mixer.music.stop()
        except Exception as e:
            print("Error stopping TTS playback:", e)
        if self.speak_thread and self.speak_thread.is_alive():
            self.speak_thread.join(timeout=0.5)

    def getmusic(self, song_term):
        videosSearch = VideosSearch(song_term, limit=2)
        results = videosSearch.result()
        video_id = results["result"][0]["id"]
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'outtmpl': 'download'
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([f'https://www.youtube.com/watch?v={video_id}'])
        pygame.mixer.music.load("download.mp3")
        pygame.mixer.music.play()
        mic_temp = sr.Microphone()
        recognizer_temp = sr.Recognizer()
        while pygame.mixer.music.get_busy():
            with mic_temp as source:
                recognizer_temp.adjust_for_ambient_noise(source)
                audio = recognizer_temp.listen(source)
                command = recognizer_temp.recognize_google(audio).lower()
                if "set alarm at" in command:
                    t = self.extract_alarm_time(command)
                    self.set_alarm(t)
                elif "set timer for" in command:
                    duration = self.extract_duration(command)
                    self.set_timer(duration)
                elif "turn on" in command or "turn off" in command:
                    entity_id = self.extract_entity(command)
                    if "turn on" in command:
                        self.turn_on_device(entity_id)
                    else:
                        self.turn_off_device(entity_id)
                elif "weather" in command:
                    self.get_weather("Ghaziabad")
                elif "time" in command:
                    self.speak(datetime.now().strftime('%I:%M %p'))
                    return datetime.now()
                elif "play" in command:
                    self.getmusic(command.replace("assistant", "").replace("play", "").strip())
                elif "stop" in command:
                    pygame.mixer.music.stop()
                else:
                    self.send_to_groqcloud(command)

    def process_command(self, command):
        print(f"Processing command: {command}")
        if "set alarm at" in command:
            self.setalarm(command)
        elif "set timer for" in command:
            duration = self.extract_duration(command)
            self.set_timer(duration)
        elif "turn on switch " in command:
            entity_id = command.replace("turn on switch", "").replace(" ", "")
            self.speak(f"Turning on {entity_id}")
            self.turnonswitch(entity_id)
        elif "turn off switch " in command:
            entity_id = command.replace("turn off switch", "").replace(" ", "")
            self.speak(f"Turning off {entity_id}")
            self.turnoffswitch(entity_id)
        elif "turn on fan" in command:
            entity_id = command.replace("turn on fan", "").replace(" ", "")
            self.speak(f"Turning on {entity_id}")
            self.turnonfan(entity_id)
        elif "turn off fan" in command:
            entity_id = command.replace("turn off fan", "").replace(" ", "")
            self.speak(f"Turning off {entity_id}")
            self.turnofffan(entity_id)
        elif "turn on light" in command:
            entity_id = command.replace("turn on light", "").replace(" ", "")
            self.speak(f"Turning on {entity_id}")
            self.turnonlight(entity_id)
        elif "turn off light" in command:
            entity_id = command.replace("turn off light", "").replace(" ", "")
            self.speak(f"Turning off {entity_id}")
            self.turnofflight(entity_id)
        elif "set colour of" in command and "to" in command:
            entandcol = command.replace("set colour of", "").replace("to", "").replace("lights", "light")
            parts = entandcol.split()
            ent = parts[0]
            color = parts[1]
            self.setcolor(ent, color)
        elif "set brightness of" in command and "to" in command:
            entandcol = command.replace("set brightness of", "").replace("to", "").replace("lights", "light")
            parts = entandcol.split()
            ent = parts[0]
            brightness = int(parts[1])
            self.lightbrightness(ent, brightness)
        elif "weather" in command:
            self.get_weather("Ghaziabad")
        elif "time" in command:
            t = datetime.now().strftime('%I:%M %p')
            self.speak(t)
        elif "play" in command:
            self.getmusic(command.replace("play", "").strip())
        elif "joke" in command:
            j = pyjokes.get_joke()
            self.speak(j)
        elif "wikipedia" in command:
            title = command.replace("ask", "").replace("wikipidia", "").replace("about", "").strip().replace("wikipedia", "")
            summary = wikipedia.summary(title, sentences=4)
            self.speak(summary)
        elif "stop" in command:
            pygame.mixer.music.stop()
        else:
            self.send_to_groqcloud(command)

    def get_weather(self, city_name="Ghaziabad"):
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city_name}&appid={self.weather_api_key}&units=metric"
        response = requests.get(url)
        weather_data = response.json()
        if weather_data["cod"] == 200:
            main_weather = weather_data["main"]
            weather_desc = weather_data["weather"][0]["description"]
            temperature = main_weather["temp"]
            humidity = main_weather["humidity"]
            weather_report = f"The current temperature in {city_name} is {temperature}°C with {weather_desc}. Humidity is {humidity}%."
            self.speak(weather_report)
            print(weather_report)
        else:
            self.speak("Sorry, I couldn't fetch the weather data.")
            print("Error fetching weather data.")

    def send_to_groqcloud(self, command):
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": command + " answer this question in 3-5 lines, but if it's incomplete just answer 'I couldn't hear you'"
                }
            ],
            model="gemma2-9b-it",
        )
        response_text = chat_completion.choices[0].message.content
        print(response_text)
        self.speak(response_text.replace("*", ""))

    def turnonlight(self, entity_id):
        with Client('http://192.168.29.128:8123/api', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiI4NDJmMTBiOTYxNDA0MTg4ODY1MTdjNzE1NmNlMzk5MCIsImlhdCI6MTc0MDMwNzgyNCwiZXhwIjoyMDU1NjY3ODI0fQ.y4Eomac86AzUI-cZnlUtbngGKGeEB_JsuAcfXxli3eI') as client:
            cos = client.get_domain("light")
            ent = "light." + entity_id
            cos.turn_on(entity_id=ent, rgb_color=[0, 0, 0])

    def turnofflight(self, entity_id):
        with Client('http://192.168.29.128:8123/api', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiI4NDJmMTBiOTYxNDA0MTg4ODY1MTdjNzE1NmNlMzk5MCIsImlhdCI6MTc0MDMwNzgyNCwiZXhwIjoyMDU1NjY3ODI0fQ.y4Eomac86AzUI-cZnlUtbngGKGeEB_JsuAcfXxli3eI') as client:
            cos = client.get_domain("light")
            ent = "light." + entity_id
            cos.turn_off(entity_id=ent)

    def turnonfan(self, entity_id):
        with Client('http://192.168.29.128:8123/api', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiI4NDJmMTBiOTYxNDA0MTg4ODY1MTdjNzE1NmNlMzk5MCIsImlhdCI6MTc0MDMwNzgyNCwiZXhwIjoyMDU1NjY3ODI0fQ.y4Eomac86AzUI-cZnlUtbngGKGeEB_JsuAcfXxli3eI') as client:
            cos = client.get_domain("fan")
            ent = "fan." + entity_id
            print(ent)
            cos.turn_on(entity_id=ent)

    def turnofffan(self, entity_id):
        with Client('http://192.168.29.128:8123/api', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiI4NDJmMTBiOTYxNDA0MTg4ODY1MTdjNzE1NmNlMzk5MCIsImlhdCI6MTc0MDMwNzgyNCwiZXhwIjoyMDU1NjY3ODI0fQ.y4Eomac86AzUI-cZnlUtbngGKGeEB_JsuAcfXxli3eI') as client:
            cos = client.get_domain("fan")
            ent = "fan." + entity_id
            print(ent)
            cos.turn_off(entity_id=ent)

    def setcolor(self, entity, color):
        with Client('http://192.168.29.128:8123/api', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiI4NDJmMTBiOTYxNDA0MTg4ODY1MTdjNzE1NmNlMzk5MCIsImlhdCI6MTc0MDMwNzgyNCwiZXhwIjoyMDU1NjY3ODI0fQ.y4Eomac86AzUI-cZnlUtbngGKGeEB_JsuAcfXxli3eI') as client:
            cos = client.get_domain("light")
            ent = "light." + entity
            rgbint = webcolors.name_to_rgb(color)
            collist = list(rgbint)
            cos.turn_on(entity_id=ent, rgb_color=collist)

    def lightbrightness(self, entity, brightness):
        with Client('http://192.168.29.128:8123/api', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiI4NDJmMTBiOTYxNDA0MTg4ODY1MTdjNzE1NmNlMzk5MCIsImlhdCI6MTc0MDMwNzgyNCwiZXhwIjoyMDU1NjY3ODI0fQ.y4Eomac86AzUI-cZnlUtbngGKGeEB_JsuAcfXxli3eI') as client:
            cos = client.get_domain("light")
            ent = "light." + entity
            lightness = round((brightness / 100) * 255)
            cos.turn_on(entity_id=ent, brightness=lightness)

    def setalarm(self, alarm_time):
        if "for" in alarm_time:
            alarm_time = alarm_time.replace("set alarm for ", "")
        else:
            alarm_time = alarm_time.replace("set alarm at ", "")
        if "p.m." in alarm_time:
            alarm_time = alarm_time.replace("p.m.", "PM")
        else:
            alarm_time = alarm_time.replace("a.m.", "AM")
        timeofal = datetime.strptime(alarm_time, "%I:%M %p").time()
        timeofal = timeofal.replace(hour=timeofal.hour % 12 + (timeofal.hour // 12) * 12)
        timeofal = str(timeofal)
        print(timeofal)
        subprocess.run(f'start powershell python time.py {timeofal}', shell=True)

    def turnonswitch(self, entity_id):
        with Client('http://192.168.29.128:8123/api', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiI4NDJmMTBiOTYxNDA0MTg4ODY1MTdjNzE1NmNlMzk5MCIsImlhdCI6MTc0MDMwNzgyNCwiZXhwIjoyMDU1NjY3ODI0fQ.y4Eomac86AzUI-cZnlUtbngGKGeEB_JsuAcfXxli3eI') as client:
            cos = client.get_domain("switch")
            ent = "switch." + entity_id
            print(ent)
            cos.turn_on(entity_id=ent)

    def turnoffswitch(self, entity_id):
        with Client('http://192.168.29.128:8123/api', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiI4NDJmMTBiOTYxNDA0MTg4ODY1MTdjNzE1NmNlMzk5MCIsImlhdCI6MTc0MDMwNzgyNCwiZXhwIjoyMDU1NjY3ODI0fQ.y4Eomac86AzUI-cZnlUtbngGKGeEB_JsuAcfXxli3eI') as client:
            cos = client.get_domain("switch")
            ent = "switch." + entity_id
            cos.turn_off(entity_id=ent)

    def extract_duration(self, command):
        if "minute" in command:
            return 60
        elif "hour" in command:
            return 3600
        return 0

    def set_timer(self, duration):
        if duration:
            self.speak(f"Timer set for {duration / 60} minutes.")
            Timer(duration, self.timer_finished).start()
        else:
            self.speak("Invalid duration for timer.")

    def timer_finished(self):
        self.speak("Your timer has finished!")

    def extract_alarm_time(self, command):
        if "time" in command:
            return datetime.now()
    def cleanup(self):
        self.audio_stream.close()
        self.pa.terminate()
        self.porcupine.delete()
        print("Resources cleaned up.")    

    def set_alarm(self, alarm_time):
        self.speak(f"Alarm set for {alarm_time}.")

    def listen_to_voice(self):
        print("Listening for 'spark' to activate...")

        try:
            while True:
                pcm = self.audio_stream.read(self.porcupine.frame_length)
                pcm = struct.unpack_from("h" * self.porcupine.frame_length, pcm)

                if self.porcupine.process(pcm) >= 0:
                    print("Wake word 'spark' detected! Now listening for commands...")

                    self.play_sound()  # Play activation sound
                    self.listen_for_commands()  # Start listening for user commands

        except KeyboardInterrupt:
            print("Stopping...")
        finally:
            self.cleanup()
                
    def listen_for_commands(self):
        while True:
            try:
                with self.mic as source:
                    self.recognizer.adjust_for_ambient_noise(source)
                    print("Listening for command...")
                    audio = self.recognizer.listen(source, phrase_time_limit=15, timeout=20)
                command = self.recognize_command(audio)
                print(f"Detected command: {command}")
                self.process_command(command)
                print("Listening for the keyword 'assistant' again...")
                break
            except sr.UnknownValueError:
                print("Could not understand the audio, please try again.")
            except sr.RequestError:
                print("Could not request results from Google Speech Recognition service.")
            except sr.WaitTimeoutError:
                print("No input detected in time. Restarting the listening loop...")
            finally:
                print("done")
                # Removed unconditional play_sound() from finally block.
                
    def recognize_command(self, audio):
        return self.recognizer.recognize_google(audio).lower()

    def play_sound(self):
        # Play the prompt sound using pygame mixer.
        pygame.mixer.music.load('plop.mp3')  # Ensure 'plop.mp3' is in the same directory.
        pygame.mixer.music.play()

if __name__ == "__main__":
    home_assistant_url = "http://192.168.29.128:8123"
    access_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiI4NDJmMTBiOTYxNDA0MTg4ODY1MTdjNzE1NmNlMzk5MCIsImlhdCI6MTc0MDMwNzgyNCwiZXhwIjoyMDU1NjY3ODI0fQ.y4Eomac86AzUI-cZnlUtbngGKGeEB_JsuAcfXxli3eI"
    groqcloud_key = "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"
    weather_api_key = "47f17fcedd2cfb3849a3ec381dc5804e"
    
    # Instantiate the assistant with the required credentials.
    assistant = Assistant(home_assistant_url, access_token, groqcloud_key, weather_api_key)
    assistant.listen_to_voice()
