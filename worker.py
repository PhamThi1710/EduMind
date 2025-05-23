from urllib.parse import urlparse

import dramatiq
from dramatiq.brokers.redis import RedisBroker
from dramatiq.middleware import AgeLimit, AsyncIO, Retries, TimeLimit

from core.settings import settings
from core.logger import syslog

redis_parameters = urlparse(settings.REDIS_URL)
syslog.info(f"Redis URL: {settings.REDIS_URL}")

middleware = [
    AsyncIO(),
    AgeLimit(max_age=3600000),  # 1 hour max age
    TimeLimit(time_limit=3600000),  # 1 hour time limit
    Retries(max_retries=3),
]
broker = RedisBroker(
    host=redis_parameters.hostname,
    port=redis_parameters.port,
    db=0,
    username=redis_parameters.username,
    password=redis_parameters.password,
    heartbeat_timeout=10000,
    middleware=middleware,
    namespace="dramatiq",
)
dramatiq.set_broker(broker)

from tasks import *
