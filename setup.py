from setuptools import setup, find_packages

setup(
    name="openai-tts",
    version="0.1.0",
    description="",
    author="Sylwester Rogalski",
    author_email="rsylwester@icloud.com",
    python_requires=">=3.12,<3.13",
    install_requires=[
        "gradio>=4.12.0,==4.12.*",
        "openai>=1.2.3,==1.2.*",
        "python-dotenv>=1.0.0,==1.0.*",
        "pydub>=0.25.1",
        "matplotlib>=3.8.3",
        "ffmpeg>=1.4",
        "tk>=0.1.0",
        "numpy~=1.0"
    ],
    packages=find_packages(),
)