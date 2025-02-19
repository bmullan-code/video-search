# video-search
Video-search demo using vector search

# Setup

## Backend
- Change into video-search directory
```bash
cd video-search
```
- create and activate a virtual environment
```bash
python -m venv env
source ./env/bin/activate
```
- Install dependencies
```bash
pip install -r requirements.txt
```

## Frontend
- change into video-search/video-search-frontend directory
```bash
cd video-search/video-search-frontend
```
- install dependencies
```bash
npm install
```

# configuration

- copy the .env.template to environment variables
```bash
cp .env.template .env
```

- edit the .env file and set your project id, location, bucket name etc. 

# setup videos

- upload your mp4 files to the bucket specified in .env 
- bucket must have read only public access (videos are served from public url)

- edit the main.py and add your list of videos
- run the python script, this will create embeddings for each video and store them in vector search
```bash
python main.py 
```
# Running 

## backend
to start the backend service 

- change into video-search directory
- run 
```bash
uvicorn service:app --reload
```

## Frontend

to run the front end (from a different terminal session)

- change into video-search/video-search-frontend directory
- run 
```bash
npm start
```
- browse to [http://localhost:3000](http://localhost:3000)