import sounddevice as sd
from scipy.io.wavfile import write
import speech_recognition as sr
import pyttsx3
import subprocess
import time
import io
import wave
import re
import random
import os
# Text-to-Speech engine using Windows built-in PowerShell (More reliable)
def speak(text):
    print(f"Ultron: {text}")
    try:
        # Remove single quotes to avoid breaking powershell command
        safe_text = text.replace("'", "")
        subprocess.run(["powershell", "-Command", f"Add-Type -AssemblyName System.speech; $speak = New-Object System.Speech.Synthesis.SpeechSynthesizer; $speak.Speak('{safe_text}')"], creationflags=subprocess.CREATE_NO_WINDOW)
    except Exception as e:
        print(f"Audio Error: {e}")

def run_adb(device, command):
    try:
        subprocess.run(f"adb -s {device} {command}", shell=True, timeout=5)
    except Exception as e:
        print(f"ADB Error: {e}")

def get_devices():
    output = subprocess.run("adb devices", shell=True, capture_output=True, text=True).stdout
    lines = output.split('\n')[1:]
    return [line.split('\t')[0] for line in lines if '\t' in line and 'device' in line]

def execute_on_all(devices, command_str, action_name):
    print(f"Executing: {action_name}")
    for dev in devices:
        run_adb(dev, command_str)
    speak(f"{action_name}. Ho gaya, aur kuch?")

def process_command(command, devices):
    if not command: return
    
    if "exit" in command or "quit" in command or "band kar" in command:
        speak("Shutting down the Ultron interface. Goodbye.")
        exit(0)

    elif "how many devices" in command or "device connected" in command or "devices connected" in command or "kitne device" in command:
        count = len(devices)
        if count == 0:
            speak("Sir, there are no devices connected currently.")
        elif count == 1:
            speak("Sir, there is exactly one device connected.")
        else:
            speak(f"Sir, there are {count} devices connected.")

    elif "who are you" in command or "kaun ho tum" in command or "kon ho tum" in command:
        speak("I am your servant.")

    # 1. SCREEN & POWER
    elif "unlock" in command or "wake" in command or "open screen" in command:
        for dev in devices:
            run_adb(dev, "shell input keyevent 224") # Wake
            time.sleep(0.5)
            run_adb(dev, "shell input swipe 500 1500 500 200") # Swipe up
        speak("Screen opened. Ho gaya, aur kuch?")
    elif "lock" in command or "screen off" in command:
        execute_on_all(devices, "shell input keyevent 26", "Screen locked")
    
    # 2. NAVIGATION
    elif "home" in command:
        execute_on_all(devices, "shell input keyevent 3", "Home button")
    elif "back" in command:
        execute_on_all(devices, "shell input keyevent 4", "Back button")
    elif "recent apps" in command:
        execute_on_all(devices, "shell input keyevent 187", "Recent apps")
    elif "scroll down" in command or "swipe down" in command:
        execute_on_all(devices, "shell input swipe 500 1500 500 300", "Scrolled down")
    elif "scroll up" in command or "swipe up" in command:
        execute_on_all(devices, "shell input swipe 500 300 500 1500", "Scrolled up")

    # 3. VOLUME & MEDIA
    elif "volume up" in command or "aawaz badhao" in command:
        execute_on_all(devices, "shell input keyevent 24", "Volume increased")
    elif "volume down" in command or "aawaz kam" in command:
        execute_on_all(devices, "shell input keyevent 25", "Volume decreased")
    elif "mute" in command:
        execute_on_all(devices, "shell input keyevent 164", "Muted")
    elif "play" in command or "pause" in command:
        execute_on_all(devices, "shell input keyevent 85", "Media play pause toggled")
    elif "next song" in command:
        execute_on_all(devices, "shell input keyevent 87", "Next track")

    # 4. APPS & LAUNCHING
    elif "open youtube" in command:
        execute_on_all(devices, "shell am start -p com.google.android.youtube", "YouTube opened")
    elif "open chrome" in command or "open google chrome" in command:
        execute_on_all(devices, "shell am start -n com.android.chrome/com.google.android.apps.chrome.Main", "Chrome opened")
    elif "open whatsapp" in command and "send" not in command:
        execute_on_all(devices, "shell am start -n com.whatsapp/.Main", "WhatsApp opened")
    elif "selfie" in command:
        for dev in devices:
            run_adb(dev, "shell input keyevent 224") # Wake screen
            time.sleep(0.5)
            # Use multiple intent flags to force front camera on different brands
            run_adb(dev, "shell am start -a android.media.action.STILL_IMAGE_CAMERA --ei android.intent.extras.CAMERA_FACING 1 --ei android.intent.extras.LENS_FACING_FRONT 1 --ez front true")
            time.sleep(4.0) # Wait 4 seconds for camera app to fully open
            run_adb(dev, "shell input keyevent 27") # Click using camera button
            time.sleep(0.5)
            run_adb(dev, "shell input keyevent 66") # Alternate click (Enter key) just in case
        speak("Selfie clicked. Ho gaya, aur kuch?")
    elif "open camera" in command or "photo" in command:
        execute_on_all(devices, "shell am start -a android.media.action.IMAGE_CAPTURE", "Camera opened")
    elif "click" in command or "capture" in command or "take a photo" in command:
        execute_on_all(devices, "shell input keyevent 27", "Photo captured")
    elif "open settings" in command:
        execute_on_all(devices, "shell am start -a android.settings.SETTINGS", "Settings opened")
    elif "bluetooth on" in command or "turn on bluetooth" in command:
        execute_on_all(devices, "shell svc bluetooth enable", "Bluetooth Turned ON")
    elif "bluetooth off" in command or "turn off bluetooth" in command:
        execute_on_all(devices, "shell svc bluetooth disable", "Bluetooth Turned OFF")
    elif "wifi on" in command or "turn on wifi" in command:
        execute_on_all(devices, "shell svc wifi enable", "Wi-Fi Turned ON")
    elif "wifi off" in command or "turn off wifi" in command:
        execute_on_all(devices, "shell svc wifi disable", "Wi-Fi Turned OFF")
    elif "open map" in command or "location" in command:
        execute_on_all(devices, "shell am start -a android.intent.action.VIEW -d 'geo:0,0?q='", "Maps opened")

    # 4.5. WHATSAPP CHATTING
    elif "send whatsapp" in command or "message on whatsapp" in command:
        msg = command.split("saying")[-1].strip() if "saying" in command else "Hello"
        msg_encoded = msg.replace(" ", "%20")
        numbers = re.findall(r'\d{10}', command.replace(" ", ""))
        if numbers:
            phone = numbers[0]
            execute_on_all(devices, f'shell am start -a android.intent.action.VIEW -d "whatsapp://send?phone=+91{phone}&text={msg_encoded}"', f"Drafting WhatsApp to {phone}")
            speak(f"WhatsApp opened with your message. Just tap send!")
        else:
            execute_on_all(devices, f'shell am start -a android.intent.action.VIEW -d "whatsapp://send?text={msg_encoded}"', "Opening WhatsApp contact picker")
            speak("Choose a contact to send the message to.")

    # 5. CALLING & SEARCHING
    elif "call" in command:
        if "nikky sis" in command or "nikki sis" in command:
            number = "9693954050"
            execute_on_all(devices, f"shell am start -a android.intent.action.CALL -d tel:{number}", "Calling Nikky Sis")
        else:
            # Extract numbers from speech if any
            numbers = re.findall(r'\d+', command)
            if numbers:
                number = "".join(numbers)
                execute_on_all(devices, f"shell am start -a android.intent.action.CALL -d tel:{number}", f"Calling {number}")
            else:
                execute_on_all(devices, "shell am start -a android.intent.action.DIAL", "Dialer opened")
            
    elif "search" in command:
        parts = command.split("search")
        query = parts[1].strip().replace(" ", "+") if len(parts) > 1 else ""
        if query:
            execute_on_all(devices, f"shell am start -a android.intent.action.VIEW -d 'https://www.google.com/search?q={query}'", f"Searching for {query}")
        else:
            speak("What do you want to search?")

    # 6. SYSTEM INFO
    elif "battery" in command:
        for dev in devices:
            out = subprocess.run(f"adb -s {dev} shell dumpsys battery | findstr level", shell=True, capture_output=True, text=True).stdout
            speak(f"Device battery is at {out.strip().split(':')[1].strip()} percent.")
            
    # 7. THE TRUE AI POWER (GEMINI INTEGRATION)
    else:
        speak("Let me think...")
        try:
            import google.generativeai as genai
            
            # Put your Gemini API Key here or set GEMINI_API_KEY environment variable!
            GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "YOUR_API_KEY_HERE")
            
            if GEMINI_API_KEY == "YOUR_API_KEY_HERE":
                speak("Sir, I need a Gemini API key to process complex commands.")
                print("\n" + "!"*40)
                print("To unlock true AI power, get a FREE API key from: https://aistudio.google.com/")
                print("And paste it into line 118 of ultron_backend.py")
                print("!"*40 + "\n")
                return
                
            genai.configure(api_key=GEMINI_API_KEY)
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            prompt = f"""
            You are Ultron, an AI assistant controlling an Android phone via ADB.
            The user said: "{command}"
            
            If they asked a conversational question (e.g. who are you, tell me a joke, what is 2+2), reply with EXACTLY:
            SPEAK: <your answer>
            
            If they asked you to do something on the phone (e.g. turn on bluetooth, take a screenshot, open instagram, write an email), reply with EXACTLY the adb shell commands needed, one per line, starting with ADB:
            Example:
            ADB: shell am start -a android.settings.BLUETOOTH_SETTINGS
            """
            
            response = model.generate_content(prompt).text
            
            for line in response.split('\n'):
                line = line.strip()
                if line.startswith("SPEAK:"):
                    speak(line.replace("SPEAK:", "").strip())
                elif line.startswith("ADB:"):
                    adb_cmd = line.replace("ADB:", "").strip()
                    execute_on_all(devices, adb_cmd, "Executing AI Command")
                    
        except Exception as e:
            speak("I encountered an error connecting to my neural network.")
            print(f"AI Error: {e}")

def listen_for_command():
    recognizer = sr.Recognizer()
    fs = 48000
    seconds = 5
    
    # Force select the Laptop's internal microphone (Microphone Array) 
    # because Windows Bluetooth headsets often throw PaErrorCode -9998 in sounddevice
    devices = sd.query_devices()
    target_device = None
    target_channels = 2
    
    for i, dev in enumerate(devices):
        if "Microphone Array" in dev['name'] and dev['max_input_channels'] >= 2:
            target_device = i
            break
                
    if target_device is not None:
        sd.default.device[0] = target_device
    else:
        target_channels = 1 # fallback if no stereo array found
    
    print("\n" + "="*40)
    print("SPEAK NOW... (Listening...)")
    print("="*40)
    try:
        myrecording = sd.rec(int(seconds * fs), samplerate=fs, channels=target_channels, dtype='int16')
        sd.wait()
        
        if myrecording.shape[1] == 2:
            myrecording = myrecording[:, 0]
            
    except Exception as e:
        print(f"Mic error: {e}")
        return input("Type command here: ").lower()
        
    print("Thinking...")
    
    wav_io = io.BytesIO()
    with wave.open(wav_io, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(fs)
        wf.writeframes(myrecording.tobytes())
    wav_io.seek(0)
    
    with sr.AudioFile(wav_io) as source:
        try:
            # Removed ambient noise adjustment because it was filtering out the voice if you spoke too early
            audio = recognizer.record(source)
            command = recognizer.recognize_google(audio, language='en-IN').lower()
            print(f"You said: '{command}'")
            return command
        except sr.UnknownValueError:
            print("Didn't catch that.")
            return ""
        except Exception as e:
            print(f"Error: {e}")
            return ""

def main():
    speak("Ultron system online. Scanning for connected devices, sir.")
    devices = get_devices()
    
    if not devices:
        speak("No devices found, sir. Please connect via USB or Wi-Fi.")
        return
        
    speak(f"All set, sir. Connected to {len(devices)} device.")
    print("\n--- AVAILABLE COMMANDS ---")
    print("Screen: 'unlock', 'lock', 'home', 'back', 'recent apps', 'scroll down', 'scroll up'")
    print("Media: 'volume up', 'volume down', 'mute', 'play', 'pause', 'next song'")
    print("Apps: 'open youtube', 'open whatsapp', 'open camera', 'open settings', 'open map'")
    print("Actions: 'take a photo' (in camera), 'call 12345', 'search [anything]', 'battery'")
    print("--------------------------\n")
    
    while True:
        cmd = listen_for_command()
        if cmd:
            process_command(cmd, devices)

if __name__ == "__main__":
    main()
