from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.date import DateTrigger

def start(update_something, date):
    scheduler = BackgroundScheduler()
    scheduler.add_job(update_something, DateTrigger(date))
    scheduler.start()