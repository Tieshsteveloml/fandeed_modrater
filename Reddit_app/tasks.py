import json
from random import randint

from celery.utils.log import get_task_logger

from Reddit_app.models import CeleryOdil, Station, Discord_user
from Reddit_app.text_analysis import master_text_analysis,master_demo_text_analysis
from celery.schedules import crontab
# from celery.decorators import task
from discord.discord import master_scraper, send_scheduled_message
from Reddit_site import celery_app
from datetime import datetime, timedelta
from Reddit_app.email_notification import send_simple_email, send_sys_email
from Reddit_app.user_digest import send_user_digest_per_station
from qa_analysis.user_analytics import analyze_user_info

logger = get_task_logger(__name__)


@celery_app.on_after_finalize.connect
def setup_periodic_tasks(sender, **kwargs):
    sender.add_periodic_task(crontab(hour=17, minute=50), task_master_scraper.s())
    # sender.add_periodic_task(crontab(hour=1, minute=5), task_send_schedule_message.s())
    sender.add_periodic_task(crontab(hour=18, minute=15), check_odil.s()) #we know its working
    sender.add_periodic_task(crontab(hour=16, minute=10, day_of_week='sat,tue,thu'), task_email_digest.s())


@celery_app.task
def task_master_scraper():
    #scheduled for everyday
    print("inside the task for master scraper")
    send_simple_email('Start scraping for discord right now',
                      'luyilousia@gmail.com', title='Discord scrape initiations')
    today = datetime.today() - timedelta(days=1)
    year=int(today.strftime("%Y"))
    month=int(today.strftime("%m"))
    day=int(today.strftime("%d"))
    try:
        master_scraper(year, month, day)
    except:
        send_simple_email('Something is wrong with master_scraper. UnCompleted discord scraping for: '+str(today), 'luyilousia@gmail.com', title='Scaper Status Failed')

@celery_app.task
def task_email_digest():
    print ("inside the task email")
    station=Station.objects.get(station_name='foundersclub')
    send_user_digest_per_station(station)
    station=Station.objects.get(station_name='suvie')
    send_user_digest_per_station(station)



@celery_app.task
def task_send_schedule_message():
    print ("inside the schedule messaging task")
    today = datetime.today()
    send_scheduled_message()


@celery_app.task
def check_odil():
    print("i am working")
    name = f"CeLeryOdil-{randint(1,1000)}"
    CeleryOdil.objects.create(name=name)


def master_analyze_user_info(obj_id, email):
    #adding the taks here
    discord_obj=Discord_user.objects.get(eid=obj_id)
    discord_name=discord_obj.discord_name
    discord_id=discord_obj.discord_id
    output_dict = json.loads(discord_obj.historical_discord_chat)
    analyze_user_info(discord_id, output_dict, pdf_report=True)
    filename = str(discord_id) + "_discord_analysis.pdf"
    send_sys_email(email, filename, discord_name)
    #return None