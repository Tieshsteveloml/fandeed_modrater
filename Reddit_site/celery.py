from __future__ import absolute_import
import os
from celery import Celery
from django.conf import settings
from celery.schedules import crontab

# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Reddit_site.settings')
app = Celery('Reddit_site')

# Using a string here means the worker will not have to
# pickle the object when using Windows.
app.config_from_object('django.conf:settings',namespace='CELERY')
app.autodiscover_tasks()


"""
app.conf.beat_schedule = {
    #'check-odil-every-minute': {
    #    'task': 'Reddit_app.tasks.check_odil',
    #    'schedule': crontab(minute='*/1')
    #},
    #'master_sraper': {
    #    'task': 'Reddit_app.tasks.task_master_scraper',
    #    #'schedule': crontab(minute=0, hour='*/12') #hour=0, minute=30
    #    'schedule': crontab(hour=17, minute=55)  # hour=0, minute=30
    #},
    #'midnight_meessage': {
    #    'task': 'Reddit_app.tasks.task_send_schedule_message',
    #    'schedule': crontab(hour=0, minute=12)
    }
}
"""

@app.task(bind=True)
def debug_task(self):
    print('Request: {0!r}'.format(self.request))
