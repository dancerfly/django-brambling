FROM python:2
ENV PYTHONUNBUFFERED 1
RUN pip install pipenv
RUN mkdir /django
WORKDIR /django
COPY Pipfile* /django/
RUN pipenv install
COPY . /code/
ENTRYPOINT ["bin/docker-entrypoint.sh"]
CMD ["./manage.py", "runserver", "0.0.0.0:8000"]
