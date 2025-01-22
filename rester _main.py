import requests
import pyttsx3
import speech_recognition as sr
from homeassistant_api import Client
from datetime import datetime
from threading import Timer
import os
from groq import Groq
import yt_dlp
from youtubesearchpython import VideosSearch
from pygame import mixer
from playsound import playsound
import pyjokes
import wikipedia

import webcolors


client= Groq(
    api_key="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",
)

class assistant:
    
    def __init__(self, home_assistant_url, access_token, groqcloud_key, weather_api_key):
        self.client = Client(home_assistant_url, access_token)
        
        self.groqcloud_key = groqcloud_key
        self.weather_api_key = weather_api_key
        self.tts_engine = pyttsx3.init()
        self.mixer = mixer.init() 
        self.recognizer = sr.Recognizer()
        self.mic = sr.Microphone()


    def speak(self, message):
        self.tts_engine.say(message)
        self.tts_engine.runAndWait()
  
        
    def getmusic(self,song_term):
        videosSearch = VideosSearch(song_term, limit = 2)
        hello = videosSearch.result()
        id=first_video_id = hello["result"][0]["id"]
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
             ydl.download([f'https://www.youtube.com/watch?v={id}'])
        mixer.music.load("download.mp3")
        mixer.music.play()
        mic = sr.Microphone()
        recognizer = sr.Recognizer()
        while mixer.music.get_busy():
          
         with mic as source:
            recognizer.adjust_for_ambient_noise(source)
            audio = recognizer.listen(source)

            command = recognizer.recognize_google(audio).lower()
            if "set alarm at" in command:
             time = self.extract_alarm_time(command)
             self.set_alarm(time)
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
              self.speak(datetime.now())
              return datetime.now()
            elif "play" in command:
           
              self.getmusic(command.replace("assistant", "").replace("play", "").strip())
           
            elif"stop" in command:
              mixer.music.stop()
              
            
            else:
              self.send_to_groqcloud(command)
            
        
                
            
                

        
        
        








    



            
    def process_command(self, command):
        print(f"Processing command: {command}")
        if "set alarm at" in command:
            time = self.extract_alarm_time(command)
            self.set_alarm(time)
        elif "set timer for" in command:
            duration = self.extract_duration(command)
            self.set_timer(duration)
        elif "turn on switch " in command:
             entity_id =command.replace("turn on switch", "")
             self.speak(f"turning on {entity_id}")
             entity_id =entity_id.replace(" ", "")
             self.turnonswitch(entity_id)
        elif "turn off switch " in command:
            
             entity_id =entity_id =command.replace("turn off switch", "")
             self.speak(f"turning off {entity_id}")
             entity_id =entity_id.replace(" ", "")             
             self.turnoffswitch(entity_id)
        elif "turn on light" in command:
            entity_id =entity_id =command.replace("turn on light", "")
            self.speak(f"turning on {entity_id}")
            entity_id =entity_id.replace(" ", "")
            self.turnonlight(entity_id)
        elif "turn off light" in command:
            entity_id =entity_id =command.replace("turn off light", "")
            self.speak(f"turning off {entity_id}")
            entity_id =entity_id.replace(" ", "")
            self.turnofflight(entity_id)
        elif "set colour of" in command and "to" in command:

            entandcol = command.replace("set colour of","").replace("to","").replace("lights","light")
            print(entandcol)
            entandcol = str(entandcol)
            colandent = entandcol.split()
            ent = colandent[0]
            color = colandent[1]
            self.setcolor(ent,color)
        elif "set brightness of" in command and "to" in command:
            entandcol = command.replace("set brightness of","").replace("to","").replace("lights","light")
            print(entandcol)
            entandcol = str(entandcol)
            colandent = entandcol.split()
            ent = colandent[0]
            brightness = int(colandent[1])
            self.lightbrightness(ent,brightness)    
             
            
            
        elif "weather" in command:
            self.get_weather("Ghaziabad")
            
        elif "time" in command:
            time =datetime.now().strftime('%I:%M %p')
            print(time)
            self.speak(time)
        elif "play" in command:
           
            self.getmusic(command.replace("play", "").strip())
        elif "joke" in command:
            a = pyjokes.get_joke()
            print(a)
            self.speak(a)
        elif "wikipedia" in command :
            titleart = command.replace("ask", "").replace("wikipidia", "").replace("about", "").strip()
            print(titleart)
            titleart = titleart.replace("wikipedia","")
            res = wikipedia.summary(titleart,sentences=4)
            print(res)
            self.speak(res)
        
            
            
        else:
            self.send_to_groqcloud(command)
            

    def get_weather(self, city_name="Ghaziabad"):
        url = f"http://api.openweathermap.org/data/2.5/weather?q=Ghaziabad&appid={self.weather_api_key}&units=metric"
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
            "content":command+"you have to answer this but if it seems that some thing got cut off  then reply:oops you missed something there keep in mind that you have to give tha answer and not ask follow up questions",
           }
         ],
         model="gemma2-9b-it",
         )   
        print(chat_completion.choices[0].message.content)
        
        self.speak(chat_completion.choices[0].message.content)
        
       
        

   


    def turnonlight(self, entity_id):
        with Client(
        'http://homeassistant.local:8123/api',
        'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJjMGU2NTE4YmNjNjk0OGE3ODA0NjVlN2MyMTYwYzY5YiIsImlhdCI6MTczNzM4MTIyMywiZXhwIjoyMDUyNzQxMjIzfQ.gvr3jtcEkEqU8zX2fCUNdJCFRgUscA9o1ZtGA0Xgx38'
        ) as client:
            cos = client.get_domain("light")
            ent = "light" + "." + entity_id
            
            cos.turn_on(entity_id=ent,rgb_color=[0,0,0])
    def turnofflight(self, entity_id):
        with Client(
        'http://homeassistant.local:8123/api',
        'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJjMGU2NTE4YmNjNjk0OGE3ODA0NjVlN2MyMTYwYzY5YiIsImlhdCI6MTczNzM4MTIyMywiZXhwIjoyMDUyNzQxMjIzfQ.gvr3jtcEkEqU8zX2fCUNdJCFRgUscA9o1ZtGA0Xgx38'
        ) as client:
            cos = client.get_domain("light")
            ent = "light" + "." + entity_id
            
            cos.turn_off(entity_id=ent)
    def setcolor(self,entity,color):
        with Client(
        'http://homeassistant.local:8123/api',
        'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJjMGU2NTE4YmNjNjk0OGE3ODA0NjVlN2MyMTYwYzY5YiIsImlhdCI6MTczNzM4MTIyMywiZXhwIjoyMDUyNzQxMjIzfQ.gvr3jtcEkEqU8zX2fCUNdJCFRgUscA9o1ZtGA0Xgx38'
        ) as client:
            cos = client.get_domain("light")
            ent = "light" + "." + entity
            rgbint = rgb_value = webcolors.name_to_rgb(color)
            collist=list(rgbint)
            cos.turn_on(entity_id=ent,rgb_color=collist)
    def lightbrightness(slef,entity,brightness):
         with Client(
        'http://homeassistant.local:8123/api',
        'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJjMGU2NTE4YmNjNjk0OGE3ODA0NjVlN2MyMTYwYzY5YiIsImlhdCI6MTczNzM4MTIyMywiZXhwIjoyMDUyNzQxMjIzfQ.gvr3jtcEkEqU8zX2fCUNdJCFRgUscA9o1ZtGA0Xgx38'
        ) as client:
            cos = client.get_domain("light")
            ent = "light" + "." + entity
            lightness=round((brightness / 100) * 255)
            cos.turn_on(entity_id=ent,brightness=lightness)
            
         
           
            
        

            
    def turnonswitch(self, entity_id):
        with Client(
        'http://homeassistant.local:8123/api',
        'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJjMGU2NTE4YmNjNjk0OGE3ODA0NjVlN2MyMTYwYzY5YiIsImlhdCI6MTczNzM4MTIyMywiZXhwIjoyMDUyNzQxMjIzfQ.gvr3jtcEkEqU8zX2fCUNdJCFRgUscA9o1ZtGA0Xgx38'
        ) as client:
            cos = client.get_domain("switch")
            ent = "switch" + "." + entity_id
            print(ent)
            cos.turn_on(entity_id=ent)
        

    def turnoffswitch(self, entity_id):
        with Client(
        'http://homeassistant.local:8123/api',
        'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJjMGU2NTE4YmNjNjk0OGE3ODA0NjVlN2MyMTYwYzY5YiIsImlhdCI6MTczNzM4MTIyMywiZXhwIjoyMDUyNzQxMjIzfQ.gvr3jtcEkEqU8zX2fCUNdJCFRgUscA9o1ZtGA0Xgx38'
        ) as client:
            cos = client.get_domain("switch")
            ent = "switch" + "." + entity_id
            
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

    def set_alarm(self, alarm_time):
        self.speak(f"Alarm set for {alarm_time}.")
        # Add actual alarm setting logic here, e.g., integration with a real alarm system.
    

    def listen_to_voice(self):
        print("Listening for 'assistant' to activate...")

        while True:
            try:
                # Continuously listen for the keyword 'assistant'
                with self.mic as source:
                    self.recognizer.adjust_for_ambient_noise(source)
                    print("Listening for keyword 'assistant'...")
                    audio = self.recognizer.listen(source, timeout=5)  # Listen for 5 seconds

                command = self.recognize_command(audio)

                print(f"Detected: {command}")

                # If 'assistant' is detected, proceed to command processing
                if "assistant" in command:
                    print("Activated! Now listening for further commands...")
                    self.play_sound()
                    self.listen_for_commands()  # Start listening for actual commands

            except sr.UnknownValueError:
                print("Could not understand the audio, please try again.")
            except sr.RequestError:
                print("Could not request results from Google Speech Recognition service.")
            except sr.WaitTimeoutError:
                print("No input detected in time. Restarting the listening loop...")  # Timeout exceeded
            finally:
                print("done")

    def listen_for_commands(self):
        # Now listen for the command after activation, without checking for 'assistant'
        while True:
            try:
                with self.mic as source:
                    self.recognizer.adjust_for_ambient_noise(source)
                    print("Listening for command...")
                    audio = self.recognizer.listen(source, phrase_time_limit=15)  # Timeout after 10 seconds of silence

                command = self.recognize_command(audio)
                print(f"Detected command: {command}")

                # Process the command
                print(self.process_command(command))

                # After processing a command, return to listening for "assistant"
                print("Listening for the keyword 'assistant' again...")
                break  # Exit the current listening loop and re-enter the first loop

            except sr.UnknownValueError:
                print("Could not understand the audio, please try again.")
            except sr.RequestError:
                print("Could not request results from Google Speech Recognition service.")
            except sr.WaitTimeoutError:
                print("No input detected in time. Restarting the listening loop...")  # Timeout exceeded
            finally:
                print("done")
                self.play_sound()

    def recognize_command(self, audio):
        # This method will recognize and return the command text from the audio input
        return self.recognizer.recognize_google(audio).lower()
    def play_sound(self):
        # Play the sound file using pygame mixer
        mixer.music.load('plop.mp3')  # Make sure 'plop.mp3' is in the same directory or provide full path
        mixer.music.play()  # Make sure 'plop.mp3' is in the same directory or provide full path

    

    
if __name__ == "__main__":
    home_assistant_url = "http://homeassistant.local:8123"
    access_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJjMGU2NTE4YmNjNjk0OGE3ODA0NjVlN2MyMTYwYzY5YiIsImlhdCI6MTczNzM4MTIyMywiZXhwIjoyMDUyNzQxMjIzfQ.gvr3jtcEkEqU8zX2fCUNdJCFRgUscA9o1ZtGA0Xgx38"
    
    groqcloud_key = "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"
    weather_api_key = "47f17fcedd2cfb3849a3ec381dc5804e"  # Add your weather API key here
   

    assistant = assistant(home_assistant_url, access_token,  groqcloud_key, weather_api_key)
    assistant.listen_to_voice()
    
