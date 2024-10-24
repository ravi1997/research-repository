
# Research Repository

This repository contains research papers, datasets, and code relevant to various projects and academic research conducted by AIIMS faculty. 


## Repository Structure

- `doc/` : Contains files for testing purpose.
- `app/` : Contains application code.
- `extra/` : Contains scripts used for testing.

## How to Use

1. **Clone the repository:**
   ```bash
   git clone https://github.com/ravi1997/research-repository.git
   ```

2. **Navigate to the relevant folder:** 
   Each project or research topic is stored in its respective folder. 

3. **Run code**: If there is any Python or Jupyter code, you can run it using the following:
   ```bash
   python -m venv env
   source env/bin/activate

   pip install -r requirements.txt

   flask db init
   flask db migrate
   flask db upgrade
   
   flask seed-db
   python wsgi.py
   ```

## Contributions

Feel free to contribute to this repository by submitting a pull request. Please ensure that your contributions align with the 
ongoing research themes.

## License

This project is licensed under the MIT License.
