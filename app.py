import os
import random
import sys
from typing import Union, Literal

import gradio as gr
import tempfile
import logging

import matplotlib
import openai
from dotenv import load_dotenv
from openai import OpenAI
from pydub import AudioSegment

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

load_dotenv()

matplotlib.use('Agg')

current_path = os.environ.get('PATH')
ffmpeg_path = os.environ.get('FFMPEG_PATH')
os.environ['PATH'] = ffmpeg_path + os.pathsep + current_path

logging.debug(f"FFmpeg path set to: {ffmpeg_path}")
logging.debug(f"Current PATH: {os.environ['PATH']}")

MAX_TEXT_LENGTH = 4000

server_name = os.getenv("SERVER_NAME", "0.0.0.0")
openai_key = os.getenv("OPENAI_KEY")

if openai_key == "<YOUR_OPENAI_KEY>":
    openai_key = ""

if openai_key == "":
    logging.error("OpenAI API key not provided.")
    sys.exit("Please Provide Your OpenAI API Key")

logging.debug("OpenAI API key loaded.")

def merge_audios(audio_files):
    logging.debug("Merging audio files...")
    combined = AudioSegment.empty()

    for audio_file in audio_files:
        try:
            sound = AudioSegment.from_mp3(audio_file.name)
            combined += sound
            logging.debug(f"Added {audio_file.name} to combined audio.")
        except Exception as e:
            logging.error(f"Error reading audio file {audio_file.name}: {str(e)}")
            raise gr.Error(f"An error occurred while merging audio files: {str(e)}")

    logging.debug("All audio files merged.")
    return combined

def split_by_length(text, length):
    splits = [text[i:i+length] for i in range(0, len(text), length)]
    logging.debug(f"Text split into {len(splits)} parts.")
    return splits

def tts(
        text: str,
        model: Union[str, Literal["tts-1", "tts-1-hd"]],
        voice: Literal["alloy", "echo", "fable", "onyx", "nova", "shimmer"],
        output_file_format: Literal["mp3", "opus", "aac", "flac"] = "mp3",
        speed: float = 1.0
):
    logging.debug(f"tts called with text length {len(text)}, model={model}, voice={voice}, "
                  f"output_file_format={output_file_format}, speed={speed}")

    if len(text) > 0 and len(text) < MAX_TEXT_LENGTH:
        try:
            logging.debug("Text length within MAX_TEXT_LENGTH, proceeding with single API call.")
            client = OpenAI(api_key=openai_key)
            logging.debug("OpenAI client initialized.")

            response = client.audio.speech.create(
                model=model,
                voice=voice,
                input=text,
                response_format=output_file_format,
                speed=speed
            )
            logging.debug("OpenAI API call successful.")

        except Exception as error:
            logging.error(f"Error during OpenAI API call: {str(error)}")
            raise gr.Error(
                "An error occurred while generating speech. Please check your API key and try again.")

        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as temp_file:
            temp_file.write(response.content)
            logging.debug(f"Response written to temporary file {temp_file.name}")

        temp_file_path = temp_file.name
        return temp_file_path

    elif len(text) > MAX_TEXT_LENGTH:
        logging.debug("Text length exceeds MAX_TEXT_LENGTH, splitting text.")
        texts: list = split_by_length(text, MAX_TEXT_LENGTH)
        audio_files = list()

        for (i, i_text) in enumerate(texts):
            try:
                logging.debug(f"Processing split {i+1}/{len(texts)}")
                client = OpenAI(api_key=openai_key)
                logging.debug("OpenAI client initialized.")

                response = client.audio.speech.create(
                    model=model,
                    voice=voice,
                    input=i_text,
                    response_format=output_file_format,
                    speed=speed
                )
                logging.debug(f"OpenAI API call successful for split {i+1}.")

            except Exception as error:
                logging.error(f"Error during OpenAI API call for split {i+1}: {str(error)}")
                raise gr.Error(
                    "An error occurred while generating speech. Please check your API key and try again.")

            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as temp_file:
                temp_file.write(response.content)
                logging.debug(f"Response for split {i+1} written to temporary file {temp_file.name}")

            audio_files.append(temp_file)

        logging.debug("All splits processed. Merging audio files.")
        audio_file = merge_audios(audio_files)

        home = os.path.expanduser("~")
        downloads = os.path.join(home, 'Downloads')

        output_file = os.path.join(downloads, f'output{random.randrange(0,10000)}.mp3')
        logging.debug(f"Exporting merged audio to {output_file}")

        try:
            audio_file.export(output_file, format='mp3')
            logging.debug("Audio file exported successfully.")
        except Exception as e:
            logging.error(f"Error exporting audio file: {str(e)}")
            raise gr.Error("An error occurred while exporting the audio file.")

        return output_file
    else:
        logging.debug("Text is empty, returning default silence audio.")
        return "1-second-of-silence.mp3"

with gr.Blocks() as demo:
    gr.Markdown("# <center> OpenAI Text-To-Speech API with Gradio </center>")
    with gr.Row(variant="panel"):
        model = gr.Dropdown(choices=["tts-1", "tts-1-hd"], label="Model", value="tts-1")
        voice = gr.Dropdown(choices=["alloy", "echo", "fable", "onyx", "nova", "shimmer"], label="Voice Options",
                            value="nova")
        output_file_format = gr.Dropdown(choices=["mp3", "opus", "aac", "flac"], label="Output Options", value="mp3")
        speed = g
