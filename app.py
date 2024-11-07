import os
import random
import sys
from typing import Union, Literal

import gradio as gr
import tempfile
import logging
import subprocess

import matplotlib
import openai
from dotenv import load_dotenv
from openai import OpenAI

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

load_dotenv()

matplotlib.use('Agg')

current_path = os.environ.get('PATH')
ffmpeg_path = os.environ.get('FFMPEG_PATH', '')
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
    logging.debug("Merging audio files using ffmpeg...")
    try:
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as list_file:
            for audio_file in audio_files:
                list_file.write(f"file '{audio_file.name}'\n")
            list_filename = list_file.name
            logging.debug(f"List of audio files written to {list_filename}")

        output_file = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False).name
        command = [
            'ffmpeg', '-y', '-f', 'concat', '-safe', '0', '-i', list_filename,
            '-c', 'copy', output_file
        ]
        logging.debug(f"Running command: {' '.join(command)}")
        subprocess.run(command, check=True)
        logging.debug("Audio files concatenated using ffmpeg.")
    except Exception as e:
        logging.error(f"Error during audio merging with ffmpeg: {str(e)}")
        raise gr.Error(f"An error occurred while merging audio files: {str(e)}")
    finally:
        # Clean up temporary files
        for audio_file in audio_files:
            os.unlink(audio_file.name)
        os.unlink(list_filename)
    return output_file

def split_by_length(text, max_length):
    import re
    sentences = re.split(r'(?<=[.!?]) +', text)
    chunks = []
    current_chunk = ''

    for sentence in sentences:
        sentence = sentence.strip()
        # If the sentence itself is longer than max_length, we need to split it further
        if len(sentence) > max_length:
            words = sentence.split()
            sentence_parts = []
            current_part = ''
            for word in words:
                if len(current_part) + len(word) + 1 <= max_length:
                    if current_part:
                        current_part += ' ' + word
                    else:
                        current_part = word
                else:
                    if current_part:
                        sentence_parts.append(current_part)
                    if len(word) <= max_length:
                        current_part = word
                    else:
                        # Split the word if it's too long
                        word_parts = [word[i:i+max_length] for i in range(0, len(word), max_length)]
                        for wp in word_parts[:-1]:
                            sentence_parts.append(wp)
                        current_part = word_parts[-1]
            if current_part:
                sentence_parts.append(current_part)
            # Add the sentence parts to chunks
            for part in sentence_parts:
                if len(current_chunk) + len(part) + 1 <= max_length:
                    if current_chunk:
                        current_chunk += ' ' + part
                    else:
                        current_chunk = part
                else:
                    if current_chunk:
                        chunks.append(current_chunk)
                    current_chunk = part
        else:
            # Check if adding the sentence exceeds the max_length
            if len(current_chunk) + len(sentence) + 1 <= max_length:
                if current_chunk:
                    current_chunk += ' ' + sentence
                else:
                    current_chunk = sentence
            else:
                # Add the current chunk to chunks and start a new chunk with the sentence
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = sentence
    # Add any remaining text to chunks
    if current_chunk:
        chunks.append(current_chunk)
    logging.debug(f"Text split into {len(chunks)} parts.")
    return chunks

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

        with tempfile.NamedTemporaryFile(suffix=f".{output_file_format}", delete=False) as temp_file:
            temp_file.write(response.content)
            temp_file_path = temp_file.name
            logging.debug(f"Response written to temporary file {temp_file_path}")

        return temp_file_path

    elif len(text) > MAX_TEXT_LENGTH:
        logging.debug("Text length exceeds MAX_TEXT_LENGTH, splitting text.")
        texts: list = split_by_length(text, MAX_TEXT_LENGTH)
        audio_files = []

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

            with tempfile.NamedTemporaryFile(suffix=f".{output_file_format}", delete=False) as temp_file:
                temp_file.write(response.content)
                logging.debug(f"Response for split {i+1} written to temporary file {temp_file.name}")

            audio_files.append(temp_file)

        logging.debug("All splits processed. Merging audio files.")
        output_file = merge_audios(audio_files)
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
        speed = gr.Slider(minimum=0.25, maximum=4.0, value=1.0, step=0.01, label="Speed")

    text = gr.Textbox(label="Input text",
                      placeholder="Enter your text and then click on the \"Text-To-Speech\" button, "
                                  "or simply press the Enter key.")
    btn = gr.Button("Text-To-Speech")
    output_audio = gr.Audio(label="Speech Output")

    text.submit(fn=tts, inputs=[text, model, voice, output_file_format, speed], outputs=output_audio, api_name="tts")
    btn.click(fn=tts, inputs=[text, model, voice, output_file_format, speed], outputs=output_audio, api_name=False)

logging.info("Launching Gradio app...")
demo.launch(server_name=server_name, share=False)
