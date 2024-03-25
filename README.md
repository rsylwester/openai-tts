# OpenAI Text To Speech API with Web UI

To manage a text with more than 4096 characters, the content would be divided into multiple sections, each with a corresponding audio file produced for it. After creating the individual audio segments, they would be merged together to form a single coherent audio file. This process ensures that the entire text, regardless of its length, can be effectively transformed into an audio format. 

## Start up Flow

1. copy `.env.example` to named file `.env`
2. put your openai api key in `.env` value `OPENAI_KEY`
3. put ffmpeg path in `.env` value `FFMPEG_PATH`
4. run `poetry install`
5. run `poetry shell`
6. type `python app.py`
7. open your browser and type [http://127.0.0.1:7860](http://127.0.0.1:7860)
8. the api docs in [http://127.0.0.1:7860/?view=api](http://127.0.0.1:7860/?view=api)


interface like this
![Screen](assets/screen.png "Screen")
