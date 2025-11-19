from celery import Celery

celery_app = Celery(broker='redis://redis:6379/0')