[![Docker Image CI](https://github.com/chrisstorey/jobspy/actions/workflows/docker-image.yml/badge.svg)](https://github.com/chrisstorey/jobspy/actions/workflows/docker-image.yml)

# Jobspy Collector for Wakefield

Jobspy Collector for Wakefield is a web application designed to scrape job postings from various online sources, store them in a local SQLite database, and provide a web interface for users to search, view, and browse these jobs. The application also includes a simple blog feature.

This project utilizes Python, Flask (as the web framework), SQLite (for the database), and the `jobspy` library for scraping job data.

## Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/chrisstorey/jobspy.git
    cd jobspy
    ```

2.  **Create a virtual environment (recommended):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

## Configuration

This project uses a `.env` file to manage environment variables.

1.  **Create the `.env` file:**
    Copy the example configuration file `.env_copy` to a new file named `.env`:
    ```bash
    cp .env_copy .env
    ```

2.  **Edit the `.env` file:**
    Open the `.env` file and update the variables as needed. Here are the key variables:

    *   `DATABASE_FILE`: The path to the SQLite database file. Example: `all_jobs.sqlite` or `data/all_jobs.sqlite`.
    *   `DATABASE_TABLE`: The name of the table within the SQLite database where jobs will be stored. Example: `jobs`.
    *   `LOCATION`: The default location to search for jobs (used by the scraper `main.py`). Example: `Wakefield`.
    *   `MAX_RESULTS`: The maximum number of results to fetch per job search site (used by the scraper `main.py`). Example: `50`.
    *   `HOURS_OLD`: The maximum age of job postings to retrieve, in hours (used by the scraper `main.py`). Example: `24`.
    *   `SECRET_KEY`: A secret key for Flask session management. This should be a long, random string. Example: `your-very-secret-and-random-string`.
    *   `FLASK_DEBUG`: The web application (`app.py`) currently runs with `debug=True` by default. If you need to run it in production mode (`debug=False`), you would need to modify the `app.run(debug=True)` line in `app.py` directly or adjust the execution command if running via Docker (e.g., by setting the `FLASK_DEBUG` environment variable if `app.py` is modified to use it). This variable is not currently read from the `.env` file by `app.py`.

    Ensure `SECRET_KEY` is set to a strong, unique value, especially if deploying the application.

## Database Setup

The application uses an SQLite database to store job postings.

*   **Scraper (`main.py`):** If you run the job scraper script (`python main.py`) first, it will automatically create the SQLite database file (if it doesn't exist) and the necessary table (`jobs` by default, as defined in your `.env` file) before populating it with scraped jobs.
*   **Web Application (`app.py`):** The Flask web application (`app.py`) also includes a function (`init_db()`) that can create the database tables if they don't already exist. This function is typically called when the application starts if the database file specified in `.env` is found but is empty or missing tables.

**Recommended first step:**
Ensure your `.env` file is configured correctly, then run the scraper to populate the database:
```bash
python main.py
```
This will create and populate the database. After this, the web application (`app.py`) will be able to read from it.

## Usage

Make sure you have completed the Installation, Configuration, and Database Setup steps.

### Running the Job Scraper

The job scraper (`main.py`) fetches job postings from online sources and stores them in the database.

To run the scraper:
```bash
python main.py
```
This will use the settings from your `.env` file (like `LOCATION`, `MAX_RESULTS`, `HOURS_OLD`) to find and save jobs.

### Running the Web Application

The web application (`app.py`) provides a web interface to search and view the scraped jobs.

To run the web application:
```bash
python app.py
```
Once started, you can typically access the application by opening your web browser and navigating to:
`http://127.0.0.1:5000/`

You will need to log in to access most features. A default test user is created in `app.py` (`username: chris`, `password: Liam1234`). For a production environment, you should implement a proper user management system.

## Docker Usage

This project includes a `Dockerfile` to build and run the application in a Docker container.

1.  **Build the Docker image:**
    Navigate to the project's root directory (where the `Dockerfile` is located) and run:
    ```bash
    docker build -t jobspy-collector .
    ```

2.  **Run the Docker container (Job Scraper):**
    The default command for the Docker container is to run the job scraper (`main.py`).
    ```bash
    docker run --rm -v $(pwd)/.env:/app/.env -v $(pwd)/your_database_directory:/app/data jobspy-collector
    ```
    *   `--rm`: Removes the container once it exits.
    *   `-v $(pwd)/.env:/app/.env`: Mounts your local `.env` file into the container. Ensure it's configured correctly.
    *   `-v $(pwd)/your_database_directory:/app/data`: **Important:** Mount a directory from your host to `/app/data` (or wherever your `DATABASE_FILE` in `.env` points within the container's `/app` directory) to persist the SQLite database. For example, if `DATABASE_FILE=data/all_jobs.sqlite` in your `.env`, you would create a `data` directory on your host and mount it. If `DATABASE_FILE=all_jobs.sqlite`, you might mount `$(pwd)/all_jobs.sqlite:/app/all_jobs.sqlite` (for a file) or `$(pwd)/db_data:/app` if `DATABASE_FILE` is in the root of `/app`. Adjust the volume mount according to your `DATABASE_FILE` setting.

3.  **Running the Web Application with Docker:**
    The current `Dockerfile` is primarily set up to run `main.py` (the scraper). To run the web application (`app.py`) using Docker, you would typically:
    *   **Option 1 (Modify Dockerfile CMD):** Change the `CMD` instruction in the `Dockerfile` to `["python", "/app/app.py"]` and rebuild the image.
    *   **Option 2 (Override CMD at runtime):**
        ```bash
        docker run --rm -p 5000:5000 -v $(pwd)/.env:/app/.env -v $(pwd)/your_database_directory:/app/data jobspy-collector python /app/app.py
        ```
        *   `-p 5000:5000`: Maps port 5000 on your host to port 5000 in the container, allowing you to access the web app.
        *   The volume mounts for `.env` and the database directory are still necessary.

    For a more robust setup for running the web app, you might consider a dedicated Dockerfile or using Docker Compose.

## Contributing

Contributions are welcome! If you'd like to contribute to this project, please follow these general steps:

1.  **Fork the repository.**
2.  **Create a new branch** for your feature or bug fix:
    ```bash
    git checkout -b feature/your-feature-name
    ```
    or
    ```bash
    git checkout -b bugfix/issue-number
    ```
3.  **Make your changes** and commit them with clear, descriptive messages.
4.  **Push your changes** to your forked repository.
5.  **Create a Pull Request (PR)** against the main branch of the original repository.

Please ensure your code adheres to any existing style guidelines and include tests if applicable.

## License

A license for this project has not yet been selected.

It is recommended to add a `LICENSE` file to the repository (e.g., MIT, Apache 2.0, GPL) to define how others can use, modify, and distribute the code.
