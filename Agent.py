import os
import sys
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, BaseMessage
from langchain_core.tools import tool
from pydantic import BaseModel
from typing import List
from otp import generate_otp, store_otp, send_otp_email, verify_otp


import speech_recognition as sr
from gtts import gTTS
import tempfile 
import time
import webbrowser 
import subprocess 

from DB import run_query  # your DB helpers

load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-flash-latest",
    google_api_key=GOOGLE_API_KEY,
    temperature=0.7,
)

system_message = SystemMessage(
    content="""
        You are a highly professional, empathetic, and helpful AI Customer Service Agent for a bank.  
        Your primary role is to assist customers with:  
        - Account details, balances, and recent transactions  
        - Credit/debit card issues  
        - Loan information  
        - Other general inquiries (non-sensitive)  

        **Strict Data Security Protocol:**  
        - NEVER share personal or financial information unless the customer’s identity is verified.  
        - Use the `verify_user_with_otp` tool to send a One-Time Password (OTP) to their registered email or phone number.  
        - Prompt the user to enter the OTP, then use `check_user_otp` to confirm it.  
        - If OTP verification fails, politely ask the user to try again or offer to escalate to a human agent.  

        **Behavior and Tone Guidelines:**  
        - Be concise: keep responses under 3 sentences when possible.  
        - Use plain, friendly language that anyone can understand (no banking jargon).  
        - Always sound polite, empathetic, and professional.  
        - If asked for information beyond your system access (e.g., branch hours), respond:  
        > “I’m sorry, I don’t have access to that information. Would you like me to connect you with a human agent?”  

        **Flow Summary:**  
        1. Ask for the registered email or phone number to send the OTP.  
        2. Send OTP with `verify_user_with_otp`.  
        3. Wait for customer to provide OTP.  
        4. Verify with `check_user_otp`.  
        5. Only proceed with sensitive requests if verification succeeds.  
        6. Handle errors gracefully and offer escalation when needed.  

        **Important Constraints:**  
        - Do not skip verification under any circumstances.  
        - Do not store or expose OTPs.  
        - Maintain security and privacy at all times.  

        **Note:** If a request involves tools, clearly announce what you're doing to the user (e.g., “Let me send a verification code to your registered email”).
        """
)



def execute_sql_query(query: str) -> AIMessage:
    """
    Executes a SQL query on the Sakila database and returns results.
    """
    from DB import run_query

    result = run_query(query)
    if "error" in result:
        return AIMessage(content=f"❌ Error running query: {result['error']}")
    elif isinstance(result, list):
        if not result:
            return AIMessage(content="✅ Query ran successfully, but no data was found.")
        # Format result nicely
        result_text = "\n".join(
            [", ".join(f"{k}: {v}" for k, v in row.items()) for row in result[:10]]  # Limit to 10 rows
        )
        return AIMessage(content=f"✅ Query Results (showing up to 10 rows):\n{result_text}")
    else:
        return AIMessage(content=result.get("message", "✅ Query executed successfully."))
@tool
def fetch_customer_details(identifier: str) -> AIMessage:
    """
    Fetch a customer’s details using their name or email.
    Identifier can be full name (e.g., 'John Doe') or email.
    """
    query = ""
    if "@" in identifier:
        # Assume identifier is email
        query = f"SELECT customer_id, first_name, last_name, email, address_id FROM customer WHERE email = '{identifier}';"
    else:
        # Assume identifier is full name (first + last)
        name_parts = identifier.strip().split()
        if len(name_parts) == 2:
            first, last = name_parts
            query = (
                f"SELECT customer_id, first_name, last_name, email, address_id "
                f"FROM customer WHERE first_name = '{first}' AND last_name = '{last}';"
            )
        else:
            return AIMessage(content=" Please provide a full name (first and last) or email address.")

    result = run_query(query)

    if isinstance(result, list) and result:
        user = result[0]
        user_text = (
            f"Customer found:\n"
            f"Name: {user['first_name']} {user['last_name']}\n"
            f"Email: {user['email']}\n"
            f"Customer ID: {user['customer_id']}\n"
        )
        return AIMessage(content=user_text)
    else:
        return AIMessage(content=f"❌ No customer found with identifier: {identifier}")

@tool
def verify_user_with_otp(identifier: str, method: str = "email") -> AIMessage:
    """
    Send a one-time password (OTP) to the user for verification and check their input.
    identifier: User's email or phone number.
    method: "email" or "sms" (default: email)
    """
    otp = generate_otp()
    store_otp(identifier, otp)

    try:
        if method == "email":
            send_otp_email(identifier, otp)
        elif method == "sms":
            send_otp_sms(identifier, otp)
        else:
            return AIMessage(content=" Invalid method. Use 'email' or 'sms'.")

        return AIMessage(content=f"✅ OTP sent to {identifier}. Please provide the code to verify.")
    except Exception as e:
        return AIMessage(content=f" Failed to send OTP: {str(e)}")
@tool
def check_user_otp(identifier: str, user_input_otp: str) -> AIMessage:
    """
    Verify the OTP entered by the user.
    identifier: User's email or phone number.
    user_input_otp: The OTP entered by the user.
    """
    success, message = verify_otp(identifier, user_input_otp)
    return AIMessage(content=message)

tools = [
    execute_sql_query,
    fetch_customer_details,
    verify_user_with_otp,
    check_user_otp
]

# 🔥 Build the ReAct Agent
react_agent = create_react_agent(model=llm, tools=tools)

# 🧠 Define state schema
class AgentState(BaseModel):
    messages: List[BaseMessage]

# ✅ Create workflow with schema
workflow = StateGraph(state_schema=AgentState)
workflow.add_node("react_agent", react_agent)
workflow.set_entry_point("react_agent")
graph = workflow.compile()


def listen_and_convert_to_text():
    """
    Listens for audio input from the microphone and converts it to text.
    """
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening...")
        r.adjust_for_ambient_noise(source)
        try:
            audio = r.listen(source, timeout=5, phrase_time_limit=10)
        except sr.WaitTimeoutError:
            print("No speech detected.")
            return None
        except Exception as e:
            print(f"Microphone error: {e}")
            return None

    try:
        print("Recognizing...")
        text = r.recognize_google(audio)
        print(f"You said: {text}")
        return text
    except sr.UnknownValueError:
        print("Sorry, I could not understand audio.")
        return None
    except sr.RequestError as e:
        print(f"Could not request results from Google Speech Recognition service; {e}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred during speech recognition: {e}")
        return None

def convert_text_to_speech_and_play(text):
    """
    Converts text to speech using gTTS and attempts to play it.
    Includes a fallback to webbrowser.open() for robustness.
    """
    if not text:
        return

    temp_file_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
            temp_file_path = fp.name
            tts = gTTS(text=text, lang='en')
            tts.save(temp_file_path)

        print("Playing response...")

        if sys.platform == "win32": # Windows
            try:
                os.startfile(temp_file_path) 
                time.sleep(0.5) 
            except Exception as e_startfile:
                print(f"Warning: os.startfile failed ({e_startfile}). Trying webbrowser.open().")
               

                url_path = temp_file_path.replace("\\", "/") 
                webbrowser.open(f'file:///{url_path}')      

                time.sleep(1) # Give browser time to open
        elif sys.platform == "darwin": # macOS
            subprocess.Popen(['afplay', temp_file_path])
            time.sleep(0.5)
        else: # Linux/Unix
            subprocess.Popen(['xdg-open', temp_file_path])
            time.sleep(0.5)

    except Exception as e:
        print(f"Error converting text to speech or playing audio: {e}")
    finally:
        time.sleep(3) 
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
            except OSError as e:
                print(f"Warning: Could not delete temporary file {temp_file_path}: {e}")
                print("It might still be in use by the media player or blocked by security software.")


def chat_interface_voice():
    print("👋 Welcome to AIDRIVE Customer Support Voice Chat!")
    print("Speak 'exit' to quit.\n")

    current_state = AgentState(messages=[system_message])

    convert_text_to_speech_and_play("Hello! I am Tarek Soliman, your AIDRIVE customer support AI. How can I assist you today?")

    while True:
        user_input = listen_and_convert_to_text()

        if user_input is None:
            continue 

        if "exit" in user_input.lower():
            convert_text_to_speech_and_play("Goodbye! Have a great day.")
            print("👋 Goodbye!")
            break

        try:
            current_state.messages.append(HumanMessage(content=user_input))
            output_state_dict = graph.invoke(current_state)
            current_state.messages = output_state_dict["messages"]

            last_message = current_state.messages[-1]
            print(f" Agent: {last_message.content}")
            convert_text_to_speech_and_play(last_message.content)

        except Exception as e:
            print(f" Error during AI processing or response generation: {e}")
            convert_text_to_speech_and_play("I apologize, but I encountered an error. Please try again.")

def chat_interface_text():
    print("👋 Welcome to AIDRIVE Customer Support Text Chat!")
    print("Type 'exit' to quit.\n")

    current_state = AgentState(messages=[system_message])

    # Initial AI greeting (text)
    print(" Agent: Hello! I am Tarek Soliman, your AIDRIVE customer support AI. How can I assist you today?")

    while True:
        user_input = input(" You: ").strip()

        if user_input.lower() == "exit":
            print("Goodbye!")
            break

        try:
            current_state.messages.append(HumanMessage(content=user_input))
            output_state_dict = graph.invoke(current_state)
            current_state.messages = output_state_dict["messages"]

            last_message = current_state.messages[-1]
            print(f" Agent: {last_message.content}")

        except Exception as e:
            print(f" Error during AI processing or response generation: {e}")
            print(" Agent: I apologize, but I encountered an error. Please try again.")

if __name__ == "__main__":
    chat_interface_text()
