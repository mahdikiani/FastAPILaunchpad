FROM python:3.11-slim as fast-base

WORKDIR /app

COPY requirements.txt requirements.txt
RUN python -m pip install --no-cache-dir -r requirements.txt 

RUN adduser --disabled-password --gecos '' user && mkdir /app/logs && chown -R user:user /app/logs

FROM fast-base as fast-server

USER user
COPY --chown=user:user . .

# CMD ["python", "-m" ,"debugpy", "--listen", "0.0.0.0:3000", "-m", "app"]
# For debugging, comment out the CMD below and uncomment the CMD above.
CMD [ "python","app.py" ]