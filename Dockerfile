# Use the official Python image from the Docker Hub
FROM sindy0514/backend-pytorch-base:latest

# Set the working directory in the container
WORKDIR /app

# Copy the pyproject.toml and uv.lock files into the container
COPY pyproject.toml uv.lock ./

# Install the dependencies using uv
RUN uv sync --frozen --verbose

# Copy the rest of the application code into the container
COPY . .

# Expose the port the application runs on
EXPOSE 5000

# Specify the command to run the application
CMD ["uv", "run", "fastapi", "run", "src/main.py"]