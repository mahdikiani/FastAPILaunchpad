FROM python:3.11-slim as fast-base

WORKDIR /app

COPY requirements.txt requirements.txt
RUN python -m pip install --no-cache-dir -r requirements.txt 

RUN adduser --disabled-password --gecos '' user

FROM fast-base as fast-server

USER user
COPY . .

CMD ["python", "-m" ,"debugpy", "--listen", "0.0.0.0:3000", "-m", "app.py"]
# CMD [ "python","app.py" ]