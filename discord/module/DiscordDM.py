import json
from random import randint, seed
from time import sleep

import discum

with open('./discord/module/sample.token.txt', 'r') as tokenfilestream:
    # Read the first line of the authorization token file.
    TOKEN = tokenfilestream.readline().rstrip()

with open('./discord/module/chat.token.txt', 'r') as tokenfilestream:
    # Read the first line of the authorization token file.
    CHAT_TOKEN = tokenfilestream.readline().rstrip()


def send_messages(message, user_id_array, guild_id=None, channel_id=None):
    bot = discum.Client(token=CHAT_TOKEN)
    user = {}
    msg_response_all_user=[]
    count_message=0
    @bot.gateway.command
    def memberTest(resp):
        if resp.event.ready_supplemental:
            user = bot.gateway.session.user
            if guild_id is not None and channel_id is not None:
                if resp.event.ready_supplemental:
                    bot.gateway.fetchMembers(guild_id,
                                             channel_id,
                                             wait=1)  # put wait=1 in params if you'd like to wait 1 second inbetween requests
                if bot.gateway.finishedMemberFetching(guild_id):
                    lenmembersfetched = len(bot.gateway.session.guild(guild_id).members)
                    print(str(lenmembersfetched) + ' members fetched')
                    bot.gateway.removeCommand(memberTest)
                    bot.gateway.close()
            else:
                bot.gateway.removeCommand(memberTest)
                bot.gateway.close()

    bot.gateway.run()

    """To Send To All Users Of A Server"""
    if guild_id is not None:
        for memberID in bot.gateway.session.guild(guild_id).members:
            if memberID == bot.gateway.session.user["id"]:
                continue
            try:
                dm_channel_id = bot.createDM([memberID]).json()["id"]
                msg_response_all_user.append(bot.sendMessage(dm_channel_id, message))
            except:
                msg_response_all_user.append(None)
                pass
            count_message=count_message+1

            seed(5)
            if count_message%10==0:
                sleep(randint(601, 900))
            else:
                sleep(randint(30, 60))

    else:
        for memberID in user_id_array:
            count_message=count_message+1
            """
            we dont need the DM_ID_MAP as chat is showing up on the same window 
            if memberID+"&"+CHAT_TOKEN in DM_ID_MAP:
                try:
                    msg_response_all_user.append(bot.sendMessage(DM_ID_MAP[memberID+"&"+TOKEN], message))  
                except:
                    msg_response_all_user.append('None')
            else:
            """
            try:
                dm_channel_id = bot.createDM([memberID]).json()["id"]
                msg_response_all_user.append(bot.sendMessage(dm_channel_id, message))
            except:
                msg_response_all_user.append(None)
                pass

            if len(user_id_array)>1:
                seed(5)
                print("sleeping to send out other messages, count message is ", count_message)
                if count_message%10==0:
                    sleep(randint(601, 900))
                else:
                    sleep(randint(30, 60))

    return msg_response_all_user
