## Book Server Python

* **Tables**
  - Users
  - Books
  - Categories
  - books_categories (for many to many)
 
* **Server Routes** (so far)
  - get users: GET /
  - create user: POST /users

*no security or sanitization of data has been done when creating user*

## To start

1. Clone the repo:
```bash
git clone <repo url>
```
2. Create python virtual environment:
```bash
python -m venv env
```
3. Install requirements.txt:
```bash
pip install -r requirements.txt
```
4. Setup the postgresql dsn **(inside main.py)** & start the server by running **python main.py**

## Packages used:
  - psycopg2
  - flask
