FROM python:3
WORKDIR /usr/src/app

RUN apt-get update && apt-get -y install cron
RUN apt-get install -y build-essential libssl-dev libffi-dev python3-dev cargo
RUN python3 -m pip install --upgrade pip


COPY Pipfile Pipfile
COPY Pipfile.lock Pipfile.lock

RUN pip install pipenv
RUN pipenv install

COPY . .
RUN chmod 0644 ./cron_scheduler
RUN crontab ./cron_scheduler

CMD printenv | grep -v "no_proxy" >> /etc/environment && cron && /usr/local/bin/pipenv run server
