import os
import uuid
from flask import Flask, request, session, Response
from flask_session import Session
from twilio.twiml.voice_response import VoiceResponse, Gather
from twilio.rest import Client
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

application = Flask(__name__)
application.secret_key = "super_secret_key"                 
application.config["SESSION_TYPE"] = "filesystem"          
Session(application)

twilio_client = Client(os.getenv("TWILIO_ACCOUNT_SID"), os.getenv("TWILIO_AUTH_TOKEN"))
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
BASE_URL = os.getenv("PUBLIC_BASE_URL", "").rstrip("/")
VOICE_WEBHOOK = f"{BASE_URL}/voice"



TWILIO_NUMBER = os.getenv("TWILIO_NUMBER")
MY_NUMBER = os.getenv("MY_PERSONAL_NUMBER")


@application.route("/")
def home():
    return "halo"

@application.post("/initiate_call")
def initiate_call():
    if not TWILIO_NUMBER:
        return "twilio number not found"
    
    data = request.get_json()
    phone_num = data.get("phone_number")
    # return phone_num

    call = twilio_client.calls.create(
        to=phone_num,
        from_=TWILIO_NUMBER,
        url=VOICE_WEBHOOK 
    )
    return  {"status": "call initiated", "sid": call.sid}


# @application.post("/voice_bot")

if __name__ == "__main__":
    application.run(port=5000)
