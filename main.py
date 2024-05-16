import psycopg2
import psycopg2.extras
import psycopg2.pool
import json
from flask import Flask
from flask import request

pool = psycopg2.pool.SimpleConnectionPool(2, 3, dbname="test", user="postgres", password="")

def create_tables():
    try:
        with pool.getconn() as conn:      
            queries = (
                # '''
                # DROP TABLE IF EXISTS users;
                # ''',
                # '''
                # DROP TABLE IF EXISTS books;
                # ''',
                # '''
                # DROP TABLE IF EXISTS categories;
                # ''',
                '''
                DROP TABLE IF EXISTS books_categories;
                ''',
                '''
                CREATE TABLE IF NOT EXISTS users (
                    id serial primary key,
                    name varchar(255),
                    gmail varchar(255) NOT NULL
                ) ''',           
                '''
                CREATE TABLE IF NOT EXISTS books (
                    id serial primary key,
                    book_name varchar(255) NOT NULL,
                    description text,
                    authorId integer,
                    foreign key (authorId) references users(id) on update cascade on delete cascade
                ) ''',
                '''            
                CREATE TABLE IF NOT EXISTS categories (
                    id serial primary key,
                    category_name varchar(255)
                )
                ''',
                '''
                CREATE TABLE IF NOT EXISTS books_categories (
                    book_id integer,
                    category_id integer,
                    primary key (book_id, category_id),
                    foreign key (book_id) references books (id) on update cascade on delete cascade,
                    foreign key (category_id) references categories (id) on update cascade on delete cascade
                )''',
            )
            with conn.cursor() as cursor:
                for query in queries:
                    cursor.execute(query)
    except (psycopg2.DatabaseError, Exception) as error:
        print(error)

def get_users_with_relations():
    command = '''
                SELECT
                    users.id,
                    users.gmail,
                    jsonb_agg(jsonb_build_object(
                        'book_name', book_categories_subquery.book_name,
                        'categories', book_categories_subquery.categories_array
                    )) AS books_with_categories
                FROM
                    users
                LEFT JOIN (
                    SELECT
                        authorId,
                        book_name,
                        jsonb_agg(categories.category_name) AS categories_array
                    FROM
                        books
                    LEFT JOIN
                        books_categories AS bc ON bc.book_id = books.id
                    LEFT JOIN
                        categories ON categories.id = bc.category_id
                    GROUP BY
                        authorId, book_name
                ) AS book_categories_subquery ON users.id = book_categories_subquery.authorId
                GROUP BY
                    users.id, users.gmail;
                '''
    try:
        with pool.getconn() as conn:      
           with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
               cursor.execute(command)
               result = cursor.fetchall()
               return json.dumps(result)
               
    except (psycopg2.DatabaseError, Exception) as error:
        print(error)
    finally:
        pool.putconn(conn)


app = Flask(__name__)

@app.get("/")
def get_users():
    resp = app.make_response(get_users_with_relations())
    resp.headers['Content-Type'] = 'application/json'
    return resp

@app.post("/users")
def create_user():
    command = "INSERT INTO users (name, gmail) VALUES(%s , %s) RETURNING *;"
    name = request.form["name"]
    gmail = request.form["gmail"]
    
    conn = pool.getconn()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute(command, vars=[name, gmail])
    conn.commit()
    pool.putconn(conn)

    result = cursor.fetchall()

    return app.make_response(result)

@app.get("/categories")
def get_categories():
    conn = pool.getconn()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute("SELECT * FROM categories;")
    result = cursor.fetchall()
    pool.putconn(conn)
    return app.make_response(result)


@app.post("/categories")
def create_category():
    command = "INSERT INTO categories (category_name) VALUES(%s) RETURNING *;"
    category_name = request.form['category_name']
    conn = pool.getconn()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    cursor.execute(command, vars=[category_name])
    conn.commit()
    pool.putconn(conn)

    return app.make_response(cursor.fetchall())

if __name__ == '__main__':
    print("Server started...")
    app.run("localhost", 4000)