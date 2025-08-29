# Use the official Python image from the Docker Hub
FROM python:3.13.0

# Set the working directory in the container
WORKDIR /app

# Install system dependencies including ffmpeg
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Install uv
RUN pip install uv

# Copy the pyproject.toml and uv.lock files into the container
COPY pyproject.toml uv.lock ./

# Install the dependencies using uv
RUN uv sync --frozen

# Copy the rest of the application code into the container
COPY . .

# Expose the port the application runs on
EXPOSE 5000

# Specify the command to run the application
CMD ["uv", "run", "fastapi", "run", "src/main.py"]