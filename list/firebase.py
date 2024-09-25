import firebase_admin
from firebase_admin import credentials

cred = credentials.Certificate("C:\Users\Lenovo\ToDo\todo-1bdea-firebase-adminsdk-fft1b-6acfeb40f1.json")
firebase_admin.initialize_app(cred)