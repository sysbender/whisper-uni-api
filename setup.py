from setuptools import setup, find_packages

setup(
    name="whisper-uni-api",
    version="0.1.0",
    description="Universal Whisper Transcription API",
    packages=find_packages(),
    install_requires=[
        "fastapi==0.104.1",
        "uvicorn[standard]==0.24.0",
        "python-multipart==0.0.6",
        "redis==5.0.0",
        "rq==1.14.0",
        "pydantic==2.5.0",
    ],
    extras_require={
        "dev": [
            "pytest==7.4.3",
            "pytest-asyncio==0.21.1",
            "httpx==0.25.2",
        ],
    },
    python_requires=">=3.11",
)

