import psycopg2

try:
    connection = psycopg2.connect(
        dbname="your_db_name",
        user="your_username",
        password="your_password",
        host="localhost",
        port="5432"
    )
    cursor = connection.cursor()

    # Begin transaction
    connection.autocommit = False

    # Execute SQL commands
    cursor.execute("INSERT INTO accounts (user_id, balance) VALUES (1, 100);")
    cursor.execute("UPDATE accounts SET balance = balance - 50 WHERE user_id = 1;")

    # Commit the transaction
    connection.commit()

except Exception as e:
    # If there's an error, rollback the transaction
    connection.rollback()
    print(f"Error: {e}")

finally:
    cursor.close()
    connection.close()
