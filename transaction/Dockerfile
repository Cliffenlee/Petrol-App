FROM python:3
WORKDIR /usr/src/app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY ./transaction.py .
COPY ./paypal.txt .
COPY ./stripe.txt .
CMD [ "python", "./transaction.py" ]