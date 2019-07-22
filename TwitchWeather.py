from TwitchWebsocket import TwitchWebsocket
import json, requests, random, logging

from enum import Enum, auto
from Log import Log
Log(__file__)

from Settings import Settings

class ResultCode(Enum):
    SUCCESS = auto()
    ERROR = auto()

class TwitchWeather:
    def __init__(self):
        # Initialize variables
        self.host = None
        self.port = None
        self.chan = None
        self.nick = None
        self.auth = None
        self.api_key = None

        # Fill uninitialized variables using settings.txt
        self.update_settings()

        # Instantiate TwitchWebsocket instance with correct params
        self.ws = TwitchWebsocket(host=self.host, 
                                  port=self.port,
                                  chan=self.chan,
                                  nick=self.nick,
                                  auth=self.auth,
                                  callback=self.message_handler,
                                  capability=None,
                                  live=True)
        
        # Start the websocket connection
        self.ws.start_bot()
        
    def update_settings(self):
        # Fill previously initialised variables with data from the settings.txt file
        self.host, self.port, self.chan, self.nick, self.auth, self.api_key = Settings().get_settings()

    def message_handler(self, m):
        try:
            if m.type == "366":
                logging.info(f"Successfully joined channel: #{m.channel}")
            
            elif m.type == "PRIVMSG":
                # Listen for command
                if m.message.startswith("!weather"):
                    split_message = m.message.split()

                    # If city params are passed
                    if len(split_message) > 1:
                        location = " ".join(split_message[1:])

                        # Get the output as well as the return code
                        out, _code = self.fetch_weather(location)
                        
                        # Send messages to Twitch chat
                        # Because in all cases, error or success, 
                        # we want to output `out` to chat, we ignore `_code` for now.
                        self.ws.send_message(out)
                    else:
                        self.ws.send_message("Please request weather for a specific city like: !weather Toronto")

        except Exception as e:
            logging.exception(e)

    def fetch_weather(self, location):
        # Construct URL and get result
        url = f"https://api.openweathermap.org/data/2.5/weather?q={location}&appid={self.api_key}"
        data = requests.get(url).json()

        # In case the city is not found
        if data['cod'] == '404':
            return data['message'].capitalize(), ResultCode.ERROR

        # If successful
        elif data['cod'] == 200:
            celcius = float(data["main"]["temp"]) - 273.15
            fahrenheit = celcius * 1.8 + 32
            humidity = float(data["main"]["humidity"])
            city = data["name"]
            country = data["sys"]["country"]
            description = data["weather"][0]["description"]
            out = f"{celcius:.1f}°C/{fahrenheit:.0f}°F, {humidity:.1f}% humidity, with {description} in {city}, {country}."
            
            return out, ResultCode.SUCCESS
        
        # If some other error (eg. api limit exceeded)
        else:
            if 'cod' in data:
                out = f"Error with code {data['cod']} encountered."
            else:
                out = "Unknown error encountered"
            return out, ResultCode.ERROR

if __name__ == "__main__":
    TwitchWeather()