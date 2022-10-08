FROM python:3.10

RUN mkdir src

COPY requirements.txt src
COPY app src/app
COPY main.py src

WORKDIR src
RUN pip install --no-cache-dir --upgrade -r requirements.txt

EXPOSE 8002
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8002"]
