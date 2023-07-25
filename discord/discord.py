from time import sleep
from datetime import timedelta, datetime
import pandas as pd
from discord.module import DiscordScraper
from os import _exit as exit
from discord.module.DiscordScraper import loads
from Reddit_app.email_notification import send_simple_email
import json
TOTAL_REQUEST_CALL=0

def getLastMessageGuild(scraper, guild, channel):
    lastmessage = 'https://discord.com/api/{0}/channels/{1}/messages?limit=1'.format(scraper.apiversion, channel)
    scraper.headers.update({'Referer': 'https://discord.com/channels/{0}/{1}'.format(guild, channel)})
    try:
        response = DiscordScraper.requestData(lastmessage, scraper.headers)
        if response is None:
            return None

        response_data = loads(response.read())

        return response_data

    except Exception as ex:
        print(ex)


def startDM(scraper, alias, channel, day=None):
    pass


def startGuild(scraper, guild, channel, day=None):
    global TOTAL_REQUEST_CALL

    snowflakes = DiscordScraper.getDayBounds(day.day, day.month, day.year)

    search = 'https://discord.com/api/{0}/channels/{1}/messages/search?min_id={2}&max_id={3}&{4}'.format(
        scraper.apiversion, channel, snowflakes[0], snowflakes[1], scraper.query)

    scraper.headers.update({'Referer': 'https://discord.com/channels/{0}/{1}'.format(guild, channel)})
    total_msg_count=0
    data=None
    try:
        scraper.grabGuildName(guild)
        scraper.grabChannelName(channel)
        if scraper.channelname == None or scraper.guildname == None:
            send_simple_email('scraper is facing a potential error, check if account has been blocked', 'luyilousia@gmail.com', title='Discord scraper potentially blocked')

        sleep(2)
        print("Making a call after 1 seconds")
        TOTAL_REQUEST_CALL=TOTAL_REQUEST_CALL+1
        print ("total requeest call in startguild is ",TOTAL_REQUEST_CALL )
        if TOTAL_REQUEST_CALL%50==0 and not TOTAL_REQUEST_CALL==0:  #this is about rate limits
            print ("avoiding, hence sleeping for 5 mins")
            sleep(180)
            print ("awake, continuee to work")

        response = DiscordScraper.requestData(search, scraper.headers)
        print ("response_status is ", response.status)
        if not response is None:
            data = loads(response.read().decode('iso-8859-1'))
            posts = data['total_results']
            if posts > 25:
                pages = int(posts / 25) + 1
                for page in range(2, pages + 1):
                    search = 'https://discord.com/api/{0}/channels/{1}/messages/search?min_id={2}&max_id={3}&{4}&offset={5}'.format(
                         scraper.apiversion, channel, snowflakes[0], snowflakes[1], scraper.query, 25 * (page - 1))
                    scraper.headers.update({'Referer': 'https://discord.com/channels/{0}/{1}'.format(guild, channel)})
                    try:
                        sleep(2)
                        TOTAL_REQUEST_CALL = TOTAL_REQUEST_CALL + 1
                        print("total requeest call in startguild is ", TOTAL_REQUEST_CALL)
                        if TOTAL_REQUEST_CALL%50==0 and not TOTAL_REQUEST_CALL==0:  # this is about rate limits
                            print("avoid 429 limits, hence sleeping for 3 mins")
                            sleep(180)
                            print("awake, continuee to work")
                        print("Downloading pages ", str(page), ": Making a call after 2 seconds")
                        response = DiscordScraper.requestData(search, scraper.headers)
                        print("response status is ", response.status)
                        data2 = loads(response.read().decode('iso-8859-1'))
                        for message in data2['messages']:
                            data['messages'].append(message)
                    except:
                        pass
            print(data)
            if posts > 0:
                total_msg_count=len(data['messages'])
    except:
        pass

    day += timedelta(days=-1)

    return day, total_msg_count, data



##################temp area
#this is just to get the member count for zilliqa, needs to be rewrite about the code
#snowflakes = DiscordScraper.getDayBounds(day.day, day.month, day.year)
#url='https://discord.com/api/v8/guilds/370992535725932544?with_counts=true'


#'approximate_member_count', 'approximate_presence_count'




def start(scraper, guild, channel, limit_year, limit_month, limit_day, day=None):
    """
    The initialization function for the scraper script.
    :param scraper: The DiscordScraper class reference that we will be using.
    :param guild: The ID for the guild that we're wanting to scrape from.
    :param channel: The ID for the channel that we're wanting to scrape from.
    """
    global TOTAL_REQUEST_CALL

    if scraper is not None:
        del scraper
        scraper = DiscordScraper()

    if day is None:
        day = datetime.today()

    if day.year <= 2014:
        exit(0)

    total_msg_count=0
    master_data=[]
    while day >= datetime(limit_year,limit_month, limit_day):
        #if TOTAL_REQUEST_CALL%50==0 and not TOTAL_REQUEST_CALL==0:
        #    print ("sleeping to avoid request limit")
        #    sleep(180)
        print ("working on ", day)
        day, msg_count, data = startGuild(scraper, guild, channel, day)
        if not data==None:
            for message in data['messages']:
                master_data.append(message[0])
            #TOTAL_REQUEST_CALL=TOTAL_REQUEST_CALL+1
        total_msg_count=total_msg_count+msg_count
        print ("agg request in start is ", TOTAL_REQUEST_CALL)
    return total_msg_count, master_data


def master_scraper(year,month,day):
    print ("in discord mod, scraping in thee masteer scraper right now")
    discordscraper = DiscordScraper()
    total_msg_count=0
    master_daily_data=[]
    for guild, channels in discordscraper.guilds.items():
        for channel in channels:
            print ("scraping channel ", channel)
            msg_count, data=start(discordscraper, guild, channel, limit_month=month, limit_year=year, limit_day=day)
            for message in data:
                master_daily_data.append(message)
            #filename='discord_'+str(channel)+'.json'
            #with open(filename, 'w') as f:
            #    json.dump(master_daily_data, f)
            total_msg_count=total_msg_count+msg_count
    print ("finishing scraping now, generating user file")
    send_simple_email("scraping is done, total scrapes "+str(total_msg_count), 'luyilousia@gmail.com', title='Discord Scrape Status')
    #updating on the new users
    try:
        server_name='Zilliqa' #could change later
        existing_data_dir='./Reddit_app/datasets/'+server_name+'.json'
        f = open(existing_data_dir)
        df = json.load(f)
        f.close()
        df=df+master_daily_data
        with open(existing_data_dir, 'w') as f:
            json.dump(df, f)
        send_simple_email("successfully updated discord db record", 'luyilousia@gmail.com', title='User DB update Success')
    except:
        send_simple_email("Failed to update discord db record", 'luyilousia@gmail.com', title='User DB update Failed')

