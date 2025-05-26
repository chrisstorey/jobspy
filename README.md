[![Docker Image CI](https://github.com/chrisstorey/jobspy/actions/workflows/docker-image.yml/badge.svg)](https://github.com/chrisstorey/jobspy/actions/workflows/docker-image.yml)

# Jobspy Collector for Wakefield

Jobspy Collector for Wakefield is a web application designed to scrape job postings from various online sources, store them in a local SQLite database, and provide a web interface for users to search, view, and browse these jobs. The application also includes a simple blog feature and user authentication.

This project utilizes Python, Flask (as the web framework), SQLite (for the database), and the `jobspy` library for scraping job data.

## Project Structure

The application has been refactored into a modular structure to improve organization and maintainability:

*   `app.py`: The main Flask application file. It initializes the Flask app, registers blueprints, and runs the development server.
*   `auth.py`: Handles all authentication-related logic, including user registration, login, logout, session management (via Flask-Login), and email validation routes.
*   `jobs.py`: Manages routes related to job searching and viewing detailed job descriptions.
*   `blog_routes.py`: Contains routes for displaying blog posts and the main index page (which lists recent blog posts).
*   `db.py`: Contains database connection logic (`get_db_connection`) and the database initialization function (`init_db`).
*   `email_utils.py`: Manages email sending functionalities (e.g., validation and welcome emails) and configures Flask-Mail.
*   `utils/utils.py`: Contains shared utility functions used across the application, such as text formatting and markdown processing.
*   `models/models.py`: Defines data models, primarily the `User` class for Flask-Login and database interaction.
*   `blog.py`: Contains the data for blog posts.
*   `main.py`: The standalone job scraping script that populates the database.
*   `templates/`: Contains HTML templates for the web interface.

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
    Open the `.env` file and update the variables as needed. Key variables include:

    *   `DATABASE_URL`: The connection string or path to the SQLite database file. Example: `instance/job_search_app.db`.
    *   `SECRET_KEY`: A secret key for Flask session management. This should be a long, random string.
    *   `MAIL_SERVER`, `MAIL_PORT`, `MAIL_USE_TLS`, `MAIL_USE_SSL`, `MAIL_USERNAME`, `MAIL_PASSWORD`, `MAIL_DEFAULT_SENDER`: Configuration for Flask-Mail to send emails.
    *   Scraper-specific variables like `LOCATION`, `MAX_RESULTS`, `HOURS_OLD` are used by `main.py`.

    Ensure `SECRET_KEY` is set to a strong, unique value. For email sending, provide valid SMTP server details.

## Database Setup

The application uses an SQLite database. The schema is defined in `db.py`.

*   **Initialization:** The `init_db()` function in `db.py` creates all necessary tables (users, jobs, etc.). This function is called automatically when `app.py` is run if the script is executed directly (i.e., `python app.py`).
*   **Scraper (`main.py`):** The job scraper script (`main.py`) also interacts with the database, populating the `jobs` table. It's recommended to run the web application once (`python app.py`) to ensure the database schema is created before running the scraper, or ensure `main.py` can also create the schema if needed.

**Recommended first step:**
Ensure your `.env` file is configured correctly, then run the web application once to initialize the database:
```bash
python app.py 
```
(The application will start, and `init_db()` will be called. You can stop it with Ctrl+C after database initialization if you wish.)
Then, run the scraper to populate the database with jobs:
```bash
python main.py
```

## Usage

Make sure you have completed the Installation, Configuration, and Database Setup steps.

### Running the Job Scraper

The job scraper (`main.py`) fetches job postings from online sources and stores them in the database.

To run the scraper:
```bash
python main.py
```
This will use the settings from your `.env` file to find and save jobs.

### Running the Web Application

The web application (`app.py`) provides a web interface to search and view jobs, and manage user accounts. `app.py` now acts as the central orchestrator, setting up the Flask application and registering blueprints from the various modules (like `auth.py`, `jobs.py`, `blog_routes.py`).

To run the web application:
```bash
python app.py
```
Once started, you can typically access the application by opening your web browser and navigating to:
`http://127.0.0.1:5000/`

User registration and login are available via the web interface. You will need to register an account and validate your email to access most features.

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
    docker run --rm --env-file .env -v $(pwd)/instance:/app/instance jobspy-collector
    ```
    *   `--rm`: Removes the container once it exits.
    *   `--env-file .env`: Passes your local `.env` file to the container.
    *   `-v $(pwd)/instance:/app/instance`: **Important:** Mount a directory from your host (e.g., `instance`) to `/app/instance` (or wherever your `DATABASE_URL` in `.env` points within the container's `/app` directory) to persist the SQLite database. This assumes `DATABASE_URL=instance/job_search_app.db`. Adjust if your path is different.

3.  **Running the Web Application with Docker:**
    To run the web application (`app.py`) using Docker, you can override the default CMD:
    ```bash
    docker run --rm -p 5000:5000 --env-file .env -v $(pwd)/instance:/app/instance jobspy-collector python /app/app.py
    ```
    *   `-p 5000:5000`: Maps port 5000 on your host to port 5000 in the container.
    *   The `--env-file` and volume mount for the database directory are still necessary.

    For a more robust setup for running the web app, consider a dedicated Dockerfile for the web application or using Docker Compose.

## Contributing

Contributions are welcome! Please follow these general steps:

1.  Fork the repository.
2.  Create a new branch for your feature or bug fix.
3.  Make your changes and commit them with clear, descriptive messages.
4.  Push your changes to your forked repository.
5.  Create a Pull Request (PR) against the main branch of the original repository.

## License

A license for this project has not yet been selected.

It is recommended to add a `LICENSE` file to the repository (e.g., MIT, Apache 2.0, GPL) to define how others can use, modify, and distribute the code.
