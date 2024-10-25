
# Backend Python Project

## Table of Contents

- [Introduction](#introduction)
- [Features](#features)
- [Technologies Used](#technologies-used)
- [Project Structure](#project-structure)
- [Installation](#installation)
- [Usage](#usage)
- [Build Instructions](#build-instructions)
- [Contributing](#contributing)
- [License](#license)

## Introduction

This is a backend Python project that provides APIs for managing publications, authors, and user structures. The project uses Flask for routing and a publication data model for managing the backend.

## Features

- API for managing publication metadata.
- API for managing author information.
- User management functionalities.
- Secure file uploads with validation.

## Technologies Used

- **Python 3.x**
- **Flask 3.0.3** (Backend framework)
- **Metapub 0.5.12** (for working with PubMed data)

## Project Structure

```
project_root/
│
├── app/
│   ├── models/
│   │   └── publication.py   # Publication data models
│   │   └── author.py        # Author data models
│   └── routes/
│       └── __init__.py      # API routes for the project
│       └── ....             # route folders for the project
│
├── requirements.txt         # Python dependencies
├── readme.md                # Documentation (this file)
└── run.py                   # Entry point for starting the app
```

## Installation

### Prerequisites

Make sure you have Python 3.x installed on your system. You will also need `pip` (Python package installer).

### Steps

1. Clone the repository:

   ```bash
   git clone https://github.com/ravi1997/research-repository.git
   cd backend-python-project
   ```

2. Create a virtual environment:

   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install the required dependencies:

   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. Run the Flask app locally:

   ```bash
   python wsgi.py
   ```

2. The application will be running at `http://127.0.0.1:5000/`.

## Build Instructions

To create a build or deploy the project, follow these steps:

1. **Install dependencies** using `requirements.txt`:

   ```bash
   pip install -r requirements.txt
   ```

2. **Run the application** using the command:

   ```bash
   python wsgi.py
   ```

3. **Deploy on a server** (if needed) using Docker or directly on a cloud platform (e.g., AWS, Heroku). Make sure to set up environment variables if required.

4. **Configure Gunicorn** (if deploying on a production server):

   Install Gunicorn:

   ```bash
   pip install gunicorn
   ```

   Run Gunicorn:

   ```bash
   gunicorn -w 4 run:app
   ```

   This will run the app with 4 worker processes.

## Contributing

Feel free to fork this repository and submit pull requests. All contributions are welcome!

## License

This project is licensed under the MIT License.
