import logging
import os


HOST_REDIS = str(os.environ.get("HOST_REDIS", "localhost"))
PORT_REDIS = int(os.environ.get("PORT_REDIS", 6379))
RABBIT_MQ = str(os.environ.get("URL_RABBIT_MQ", "amqp://guest:guest@127.0.0.1/"))
PROXY_CONTA = str(os.environ.get("PROXY_CONTA", "http://localhost:8003/"))
PROXY_DEBITO = str(os.environ.get("PROXY_DEBITO", "http://localhost:8003/debita-conta"))
PROXY_CREDITO = str(os.environ.get("PROXY_CREDITO", "http://localhost:8003/credita-conta"))
HOST_JAEGER = str(os.environ.get("HOST_JAEGER", "localhost"))
PORT_JAEGER = int(os.environ.get("PORT_JAEGER", 6831))
URL_PG = str(os.getenv("SQL_DB", "postgresql+asyncpg://bwcelvdd:uwjUQ68ABrTdaqwVLXpOtgDHxDNWvPGd@kesavan.db.elephantsql.com/bwcelvdd"))

logger = logging.getLogger('python-logstash-logger')
logger.setLevel(logging.ERROR)
