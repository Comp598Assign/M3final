FROM python

COPY /app .
RUN pip install flask
RUN pip freeze > requirements.txt
RUN pip3 install -r requirements.txt
CMD ["python3", "-m", "flask", "app.py", "15000"]