import logging
import os


HOST_REDIS = str(os.environ.get("HOST_REDIS", "localhost"))
PORT_REDIS = int(os.environ.get("PORT_REDIS", 6379))
RABBIT_MQ = str(os.environ.get("URL_RABBIT_MQ", "amqp://guest:guest@127.0.0.1/"))
HOST_JAEGER = str(os.environ.get("HOST_JAEGER", "localhost"))
PORT_JAEGER = int(os.environ.get("PORT_JAEGER", 6831))

logger = logging.getLogger('python-logstash-logger')
logger.setLevel(logging.ERROR)
