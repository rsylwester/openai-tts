import os
import random
import sys
from typing import Union, Literal

import gradio as gr
import tempfile

import matplotlib
import openai
from dotenv import load_dotenv
from openai import OpenAI
from pydub import AudioSegment

load_dotenv()

matplotlib.use('Agg')

current_path = os.environ.get('PATH')
ffmpeg_path = os.environ.get('FFMPEG_PATH')
os.environ['PATH'] = ffmpeg_path + os.pathsep + current_path

MAX_TEXT_LENGTH = 4000

server_name = os.getenv("SERVER_NAME", "0.0.0.0")
openai_key = os.getenv("OPENAI_KEY")

if openai_key == "<YOUR_OPENAI_KEY>":
    openai_key = ""

if openai_key == "":
    sys.exit("Please Provide Your OpenAI API Key")


def merge_audios(audio_files):
    combined = AudioSegment.empty()

    for audio_file in audio_files:
        sound = AudioSegment.from_mp3(audio_file.name)
        combined += sound

    return combined

def split_by_length(text, length):
    return [text[i:i+length] for i in range(0, len(text), length)]


def tts(
        text: str,
        model: Union[str, Literal["tts-1", "tts-1-hd"]],
        voice: Literal["alloy", "echo", "fable", "onyx", "nova", "shimmer"],
        output_file_format: Literal["mp3", "opus", "aac", "flac"] = "mp3",
        speed: float = 1.0
):
    if len(text) > 0 and len(text) < MAX_TEXT_LENGTH:
        try:
            client = OpenAI(api_key=openai_key)

            response = client.audio.speech.create(
                model=model,
                voice=voice,
                input=text,
                response_format=output_file_format,
                speed=speed
            )

        except Exception as error:
            print(str(error))
            raise gr.Error(
                "An error occurred while generating speech. Please check your API key and come back try again.")

        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as temp_file:
            temp_file.write(response.content)

        temp_file_path = temp_file.name

        return temp_file_path
    elif len(text) > MAX_TEXT_LENGTH:

        texts: list = split_by_length(text, MAX_TEXT_LENGTH)
        audio_files = list()

        for (i, i_text) in enumerate(texts):
            try:
                client = OpenAI(api_key=openai_key)

                response = client.audio.speech.create(
                    model=model,
                    voice=voice,
                    input=i_text,
                    response_format=output_file_format,
                    speed=speed
                )

            except Exception as error:
                print(str(error))
                raise gr.Error(
                    "An error occurred while generating speech. Please check your API key and come back try again.")

            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as temp_file:
                temp_file.write(response.content)

            print(f"audio_file {i}: " + temp_file.name)
            audio_files.append(temp_file)

        audio_file = merge_audios(audio_files)

        home = os.path.expanduser("~")
        downloads = os.path.join(home, 'Downloads')

        output_file = os.path.join(downloads, f'output{random.randrange(0,10000)}.mp3')
        print(f"output TTS file: {output_file}")

        audio_file.export(output_file, format='mp3')

        return output_file
    else:
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

demo.launch(server_name=server_name, share=False)

