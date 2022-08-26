FROM python:3
WORKDIR /usr/src/app

RUN apt-get update && apt-get -y install cron

COPY .env .env
COPY Pipfile Pipfile
COPY Pipfile.lock Pipfile.lock

RUN pip install pipenv
RUN pipenv install

COPY . .
RUN chmod 0644 ./cron_scheduler
RUN crontab ./cron_scheduler

CMD cron && /usr/local/bin/pipenv run server