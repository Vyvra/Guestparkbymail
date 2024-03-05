# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set the working directory to /app
WORKDIR /app

# Clone the GitHub repository
RUN apt-get update && apt-get install -y git 
RUN git clone https://github.com/Vyvra/Guestparkbymail.git .

# Install any dependencies
RUN pip install --no-cache-dir -r requirements.txt
#COPY config.yaml /app/config.yaml

# Run app.py when the container launches
#CMD ["flask", "--app", "api.py", "run", "&!", "python", "parkapp.py"]
CMD ["bash", "-c", "flask --app api.py run & python parkapp.py"]
