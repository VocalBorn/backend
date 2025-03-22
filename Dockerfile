# Use the official Python image from the Docker Hub
FROM python:3.13.0

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install the dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
COPY . .

# Expose the port the application runs on
EXPOSE 5000

# Specify the command to run the application
CMD ["fastapi", "run", "src/main.py"]