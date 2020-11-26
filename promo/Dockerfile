FROM python:3
WORKDIR /usr/src/app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY ./promotions.py .
EXPOSE 5000
CMD [ "python", "./promotions.py" ]
