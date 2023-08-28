# Use an official Python runtime as a parent image
FROM python:3.10.6



# Use an official Gdal as a base image
FROM osgeo/gdal:ubuntu-small-latest

RUN apt-get update && apt-get install -y build-essential libcairo2-dev pkg-config
RUN apt-get update && apt-get -y install python3-pip --fix-missing

RUN apt-get update && apt-get install -y postgresql-server-dev-all
RUN pip install pycairo
# Set the working directory to /app
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
# RUN apt-get install -y gdal-bin libgdal-dev

# Make port 9006 available to the world outside this container
EXPOSE 8000


# Start the Django server
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]



# Step to Create docker images  
# docker pull osgeo/gdal:ubuntu-small-latest
# docker run -it osgeo/gdal:ubuntu-small-latest
# docker build --tag webgram:latest .
# docker image ls
# docker run --name webgram -d -p 9006:9006 webgram:latest 
# docker container ps


# to push the image to the registry

# docker tag claimassure jafarkhan0/claimassure_v1
# docker push jafarkhan0/claimassure_v1
