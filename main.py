import tkinter as tk
from PIL import Image, ImageTk
import sys
import speech_recognition as sr
import threading
import os
import openai
import pyttsx3
import time


class VoiceAssistant:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Hey Genie")
        self.recognizer = sr.Recognizer()
        self.is_running = True

        # Initialize OpenAI
        openai.api_key = 'your-api-key-here'

        self.initialize_tts()

        # Set window size and position it in center of screen
        window_width = 350
        window_height = 450
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        center_x = int(screen_width/2 - window_width/2)
        center_y = int(screen_height/2 - window_height/2)
        self.root.geometry(f'{window_width}x{window_height}+{center_x}+{center_y}')

        # Create a label for the "Hey Genie" text
        label = tk.Label(self.root, text="Hey Genie", font=("Arial", 24))
        label.pack(pady=20)

        # Add mic control button
        self.is_mic_active = True  # New class variable
        self.mic_button = tk.Button(
            self.root, 
            text="Mute Mic", 
            command=self.toggle_mic,
            bg="red",
            fg="white",
            font=("Arial", 10)
        )
        self.mic_button.pack(pady=10)

        # Create a label for the genie image
        try:
            image = Image.open("genie.png")
            image_width = 200
            aspect_ratio = image.height / image.width
            image_height = int(image_width * aspect_ratio)
            image = image.resize((image_width, image_height), Image.Resampling.LANCZOS)
            
            self.genie_image = ImageTk.PhotoImage(image)
            
            self.image_label = tk.Label(self.root, image=self.genie_image)
            self.image_label.pack(pady=20)
        except FileNotFoundError:
            print("Error: genie.png not found in the current directory")
            error_label = tk.Label(self.root, text="Image not found!", font=("Arial", 12), fg="red")
            error_label.pack(pady=20)
        except Exception as e:
            print(f"Error loading image: {str(e)}")
            error_label = tk.Label(self.root, text="Error loading image!", font=("Arial", 12), fg="red")
            error_label.pack(pady=20)

        # Create status label to show recording status
        self.status_label = tk.Label(self.root, text="Listening...", font=("Arial", 12))
        self.status_label.pack(pady=10)

        # Create response label to show AI responses
        self.response_label = tk.Label(self.root, text="", font=("Arial", 10), wraplength=280)
        self.response_label.pack(pady=10)

        # Handle window closing
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Start recording in a separate thread
        self.recording_thread = threading.Thread(target=self.recording)
        self.recording_thread.daemon = True
        self.recording_thread.start()

    def initialize_tts(self):
        #Initialize text-to-speech engine
        try:
            self.engine = pyttsx3.init()
            self.engine.setProperty("rate", 125)  # Speed of speech
            self.engine.setProperty("volume", 1.0)  # Volume level
            
            # Set female voice if available
            voices = self.engine.getProperty('voices')
            if len(voices) > 1:  # Check if there are multiple voices available
                self.engine.setProperty('voice', voices[1].id)  # Set to female voice
            
            print("Text-to-speech engine initialized successfully")
        except Exception as e:
            print(f"Error initializing text-to-speech engine: {str(e)}")
            self.engine = None

    def speak(self, text):
        #Function to convert text to speech

        try:
            # Create a new thread for text-to-speech to prevent GUI freezing
            tts_thread = threading.Thread(target=self._speak_thread, args=(text,))
            tts_thread.daemon = True
            tts_thread.start()
        except Exception as e:
            print(f"Error in text-to-speech: {str(e)}")

    def _speak_thread(self, text):
        #Internal function to handle text-to-speech in a separate thread

        try:
            self.engine.say(text)
            self.engine.runAndWait()
        except Exception as e:
            print(f"Error in text-to-speech thread: {str(e)}")
            self.initialize_tts()

    def call_openai(self, user_input):
        #Function to call OpenAI API with the user's input

        try:
            self.status_label.config(text="Processing...")
            
            # Make API call to OpenAI
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                temperature= 0.7,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Your name is Genie"
                            "Say Hey kid in your response"
                            "You are a friendly assistant who talks in a way that is easy for kids to understand. "
                            "Always keep your responses positive, simple, and free from content that may be inappropriate for children. "
                            "Avoid topics or words related to violence, sensitive issues, or adult themes."
                        )
                    },
                    {"role": "user", "content": user_input}
                ],
            )
         
            # Get the response text
            ai_response = response.choices[0].message.content
            
            print(ai_response)
            # Update the response label with AI's response
            self.status_label.config(text="Listening...")
            
            # Speak the response
            self.speak(ai_response)
            return ai_response

        except Exception as e:
            print(f"Error in OpenAI call: {str(e)}")
            self.response_label.config(text="Sorry, I encountered an error.")
            self.status_label.config(text="Listening...")
            return None

    def toggle_mic(self):
        #Function to toggle microphone state
        self.is_mic_active = not self.is_mic_active
        if self.is_mic_active:
            self.mic_button.config(text="Mute Mic", bg="red")
            self.status_label.config(text="Listening...")
        else:
            self.mic_button.config(text="Unmute Mic", bg="gray")
            self.status_label.config(text="Microphone Muted")


    def recording(self):
        #Function to check mic status and record voice command

        while self.is_running:
            if not self.is_mic_active:
                self.status_label.config(text="Microphone Muted")
                time.sleep(0.1)
                continue
                
            with sr.Microphone() as source:
                try:
                    self.status_label.config(text="Listening...")
                    audio = self.recognizer.listen(source)
                    
                    # Check mic state again after getting audio
                    if not self.is_mic_active:
                        continue
                        
                    try:
                        text = self.recognizer.recognize_google(audio)
                        
                        # Final check before processing
                        if not self.is_mic_active:
                            continue
                            
                        print("You said:", text)
                        #self.process_voice_command(text)
                        self.call_openai(text)

                    except sr.UnknownValueError:
                        if self.is_mic_active:  # Only show error if mic is still active
                            print("Sorry, I could not understand.")
                            self.status_label.config(text="Sorry, I could not understand.")
                            
                except Exception as e:
                    if not self.is_running:
                        break
                    if self.is_mic_active:  # Only show error if mic is still active
                        print(f"Error occurred: {str(e)}")
                        self.status_label.config(text="Error occurred while listening")



    def on_closing(self):
        print("Closing application...")
        self.is_running = False
        self.root.destroy()
        sys.exit()

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = VoiceAssistant()
    app.run()