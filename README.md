# Job Collector

[![Docker Image CI](https://github.com/chrisstorey/jobspy/actions/workflows/docker-image.yml/badge.svg)](https://github.com/chrisstorey/jobspy/actions/workflows/docker-image.yml)

This is a job collector application that scrapes job data from various sites and displays it in a web interface. The backend is built with FastAPI.

## Running the Application

To run the application, you will need to have Python 3.10+ installed. You will also need to install the dependencies in `requirements.txt`.

```bash
pip install -r requirements.txt
```

Once the dependencies are installed, you can run the application with the following command:

```bash
uvicorn main_fastapi:app --reload
```

The application will be available at `http://localhost:8080`.
