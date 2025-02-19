# video-search
video-search

# setup

## backend
- change into video-search directory
cd video-search
- create a virtual environment
python -m venv env
. ./env/bin/activate
pip install -r requirements.txt

## frontend
- change into video-search/video-search-frontend directory
cd video-search/video-search-frontend
- install dependencies
npm install


# configuration

- copy the .env.template
cp .env.template .env

- edit the .env file and set your project id, location, bucket name etc. 

# setup videos

- upload your mp4 files to the bucket specified in .env (copy to top level path)
- bucket must have read only public access (videos are served from public url)

- edit the main.py and add your list of videos
- run the python script, this will create embeddings for each video and store them in vector search
python main.py 

# running 

## backend
to start the backend service 

- change into video-search directory
- run 'uvicorn service:app --reload'

## frontend

to run the front end (from a different terminal session)

- change into video-search/video-search-frontend directory
- run 'npm start'
- browse to http://localhost:3000