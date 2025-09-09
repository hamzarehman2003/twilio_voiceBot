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
VOICE_WEBHOOK = f"{BASE_URL}/voice_bot"
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

    call = twilio_client.calls.create(
        to=phone_num,
        from_=TWILIO_NUMBER,
        url=VOICE_WEBHOOK 
    )
    return  {"status": "call initiated", "sid": call.sid}


@application.post("/voice_bot")
def voice_bot():
    response = VoiceResponse()
    if "session_id" not in session:
        session["session_id"] = str(uuid.uuid4())
        session["history"] = [
            {"role": "system", "content": "You are a concise, friendly voice assistant."}
        ]

    user_input = request.form.get("SpeechResult")
    if user_input:
        session["history"].append({"role": "user", "content": user_input})
        if "goodbye" in user_input.lower():
            response.say("Goodbye, have a nice day!")
            # Notify via SMS
            if MY_NUMBER and TWILIO_NUMBER:
                twilio_client.messages.create(
                    to=MY_NUMBER,
                    from_=TWILIO_NUMBER,
                    body=f"Call ended. Session ID: {session['session_id']}"
                )
            response.hangup()
            return Response(str(response), mimetype="application/xml")

        # Get assistant reply from OpenAI
        completion = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=session["history"]
        )
        bot_reply = completion.choices[0].message.content
        session["history"].append({"role": "assistant", "content": bot_reply})
        response.say(bot_reply)

    gather = response.gather(input="speech", action=VOICE_WEBHOOK, speechTimeout="auto")
    response.append(gather)
    return Response(str(response), mimetype="application/xml")
if __name__ == "__main__":
    application.run(port=5000)
