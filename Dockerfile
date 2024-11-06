# Use an official Python runtime as a parent image
FROM python:3.8-slim

# Install system dependencies for audio processing and FFmpeg
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

# Set the FFMPEG_PATH environment variable
ENV FFMPEG_PATH=/usr/bin/ffmpeg

# Set the working directory in the container
WORKDIR /usr/src/app

# Copy the current directory contents into the container at /usr/src/app
COPY . .

# Install dependencies
RUN pip install -r requirements.txt

# Make port 7860 available to the world outside this container
EXPOSE 7860

# Run app.py when the container launches
CMD ["python", "app.py"]
#CMD ["tail", "-f", "/dev/null"]

