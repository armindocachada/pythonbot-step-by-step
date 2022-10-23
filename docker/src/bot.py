# This example requires the 'message_content' intent.

import re
import discord
from discord.ext import tasks
#from threading import Thread
from time import sleep
import json
from badminton_court_finder import findAvailableSlots
import json
from dateutil import parser

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

def searchForAvailabilityOfBadmintonCourts():
    
    json_response = findAvailableSlots(["Erith","Sidcup"], numberOfDaysInFuture=5, slots=1, earliestTime="19:00", latestTime="21:00", numberOfHours=2 )

    # [{"Date":"26 Oct 2022","Location":"Erith","Time":"2022-10-26T20:00:00.000Z","Availability":4,"Max Duration":2}]
    json_response_obj = json.loads(json_response)

    messages = []
    for available_time in json_response_obj:
        date = available_time["Date"]
        time = available_time["Time"]
        time_obj = parser.parse(time)
        date_to_str = time_obj.strftime("%H:%M")
    
        number_of_courts= available_time["Availability"]
        max_duration=available_time["Max Duration"]
        location = available_time["Location"]
        response_item = f"There is availability in {location} on the {date} at {date_to_str} for {number_of_courts} court(s) for {max_duration}h"
        messages.append(response_item)


    return messages


class MyClient(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # an attribute we can access from our task
        self.counter = 0

    async def setup_hook(self) -> None:
        # start the task to run in the background
        self.do_badminton_courts_search.start()

    async def on_ready(self):
        print(f'Logged in as {self.user} (ID: {self.user.id})')
        print('------')

    @tasks.loop(seconds=1800)  # task runs every 30 minutes
    async def do_badminton_courts_search(self):
        print("do_badminton_courts_search=I am being called")
        channel = self.get_channel(1033492628823621733)  # channel ID goes here
        try: 
            messages = searchForAvailabilityOfBadmintonCourts()
            for message in messages:
                await channel.send(message)
        except Exception as e:
            print(e)


    @do_badminton_courts_search.before_loop
    async def before_my_task(self):
        await self.wait_until_ready()  # wait until the bot logs in








if __name__ == "__main__":
    # thread = Thread(target = do_badminton_courts_search, args = (10, ))
    # thread.start()
    credentials = dict(line.strip().split('=') for line in open('leisure_centre.properties'))
    client = MyClient(intents=discord.Intents.default())
    
    client.run(credentials["discord_bot_token"])

