### 1. **Data Types**

- **Textual Data**:
  - PostgreSQL uses `TEXT` or `VARCHAR` for variable-length strings, and `CHAR` for fixed-length strings.
  - SQL Server uses `VARCHAR`, `NVARCHAR` (for Unicode), and `CHAR`.

- **Boolean Data Type**:
  - PostgreSQL has a `BOOLEAN` data type (`TRUE`, `FALSE`, or `NULL`).
  - SQL Server does not have a `BOOLEAN` data type. Instead, it uses `BIT`, where `0` is `FALSE` and `1` is `TRUE`.

- **Auto-Incrementing Primary Keys**:
  - PostgreSQL uses the `SERIAL` or `BIGSERIAL` data types for auto-incrementing primary keys.
  - SQL Server uses `IDENTITY` for auto-incrementing columns.

  ```sql
  -- PostgreSQL:
  CREATE TABLE users (
      id SERIAL PRIMARY KEY,
      name VARCHAR(100)
  );

  -- SQL Server:
  CREATE TABLE users (
      id INT IDENTITY(1,1) PRIMARY KEY,
      name VARCHAR(100)
  );
  ```

### 2. **String Concatenation**

- **PostgreSQL**:
  - Uses the `||` operator for string concatenation.

  ```sql
  SELECT 'Hello' || ' ' || 'World';
  ```

- **SQL Server**:
  - Uses the `+` operator for string concatenation.

  ```sql
  SELECT 'Hello' + ' ' + 'World';
  ```

### 3. **Limit and Offset for Pagination**

- **PostgreSQL** uses `LIMIT` and `OFFSET` for pagination:
  ```sql
  SELECT * FROM users LIMIT 10 OFFSET 20;
  ```

- **SQL Server** (modern versions) uses `OFFSET` and `FETCH NEXT`:
  ```sql
  SELECT * FROM users
  ORDER BY id
  OFFSET 20 ROWS
  FETCH NEXT 10 ROWS ONLY;
  ```

  In older versions of SQL Server, you had to use a combination of `ROW_NUMBER()` or more complex methods for pagination.

### 4. **Upsert (INSERT ON CONFLICT / MERGE)**

- **PostgreSQL** uses `INSERT ... ON CONFLICT` for upsert operations (insert if the row doesn't exist, otherwise update):

  ```sql
  INSERT INTO users (id, name)
  VALUES (1, 'Alice')
  ON CONFLICT (id)
  DO UPDATE SET name = EXCLUDED.name;
  ```

- **SQL Server** uses `MERGE` for similar functionality:

  ```sql
  MERGE INTO users AS target
  USING (VALUES (1, 'Alice')) AS source (id, name)
  ON target.id = source.id
  WHEN MATCHED THEN
      UPDATE SET name = source.name
  WHEN NOT MATCHED THEN
      INSERT (id, name) VALUES (source.id, source.name);
  ```

### 5. **Date and Time Functions**

- **Current Date/Time**:
  - PostgreSQL uses `CURRENT_TIMESTAMP`, `NOW()`, `CURRENT_DATE`.
  - SQL Server uses `GETDATE()` for the current date and time, and `SYSDATETIME()` for more precision.

- **Date Difference**:
  - PostgreSQL uses `AGE()`, or `DATE_PART()`.
  - SQL Server uses `DATEDIFF()`.

  ```sql
  -- PostgreSQL:
  SELECT AGE('2024-01-01', '2023-01-01');

  -- SQL Server:
  SELECT DATEDIFF(YEAR, '2023-01-01', '2024-01-01');
  ```

### 6. **Joining Multiple Tables**

PostgreSQL and SQL Server both support `JOIN`, but there’s a notable difference in the use of `FULL OUTER JOIN`:

- **PostgreSQL**:
  ```sql
  SELECT * FROM table1
  FULL OUTER JOIN table2 ON table1.id = table2.id;
  ```

- **SQL Server**:
  This is the same in SQL Server:
  ```sql
  SELECT * FROM table1
  FULL OUTER JOIN table2 ON table1.id = table2.id;
  ```

However, SQL Server tends to have more complex functionality for joining large datasets or specific use cases (e.g., table hints, locking hints).

### 7. **Stored Procedures vs. Functions**

- **PostgreSQL**:
  - PostgreSQL uses `FUNCTION` for both returning values and executing logic (like stored procedures).
  - Stored procedures were introduced in PostgreSQL 11 with the `CALL` statement.

  ```sql
  CREATE FUNCTION my_function() RETURNS INTEGER AS $$
  BEGIN
    RETURN 42;
  END;
  $$ LANGUAGE plpgsql;
  ```

- **SQL Server**:
  - SQL Server has separate `PROCEDURE` and `FUNCTION` constructs.
  
  ```sql
  -- Stored procedure:
  CREATE PROCEDURE my_procedure
  AS
  BEGIN
    SELECT 42;
  END;

  -- Function:
  CREATE FUNCTION my_function() RETURNS INT
  AS
  BEGIN
    RETURN 42;
  END;
  ```

### 8. **Handling NULL Values**

- **PostgreSQL**:
  - Uses `IS DISTINCT FROM` to compare `NULL` values as if they were non-null.
  
  ```sql
  SELECT * FROM users WHERE name IS DISTINCT FROM 'John';
  ```

- **SQL Server**:
  - Does not have `IS DISTINCT FROM`, but uses `ISNULL()` to replace `NULL` values.
  
  ```sql
  SELECT ISNULL(name, 'default_value') FROM users;
  ```

### 9. **CTE (Common Table Expressions)**

Both PostgreSQL and SQL Server support **CTEs** (`WITH` clauses), and the syntax is nearly identical:

```sql
WITH cte AS (
    SELECT * FROM users WHERE age > 30
)
SELECT * FROM cte;
```

### 10. **Case Sensitivity**

- **PostgreSQL** is case-sensitive by default for identifiers unless you quote them.
  
  ```sql
  CREATE TABLE "MyTable" (id SERIAL);
  ```

- **SQL Server** is case-insensitive for identifiers, but case-sensitive for data if the collation is set to case-sensitive.

### Summary of Key Differences:

| Feature                          | PostgreSQL Syntax                          | SQL Server Syntax                      |
|----------------------------------|--------------------------------------------|----------------------------------------|
| Auto-Increment                   | `SERIAL`                                   | `IDENTITY`                             |
| String Concatenation             | `||`                                       | `+`                                    |
| Pagination                       | `LIMIT` + `OFFSET`                         | `OFFSET ... FETCH`                     |
| Upsert                           | `INSERT ... ON CONFLICT`                   | `MERGE`                                |
| Current Date/Time                | `NOW()`, `CURRENT_TIMESTAMP`               | `GETDATE()`, `SYSDATETIME()`           |
| Date Difference                  | `AGE()`, `DATE_PART()`                     | `DATEDIFF()`                           |
| Functions/Procedures             | `FUNCTION` (and `PROCEDURE` from v11)       | Separate `FUNCTION` and `PROCEDURE`    |
| NULL Handling                    | `IS DISTINCT FROM`                         | `ISNULL()`                             |
| Case Sensitivity                 | Case-sensitive by default                  | Case-insensitive (collation dependent) |

### 11. Documentation:
  - [installation](https://www.postgresql.org/download/linux/redhat/)
  - [filling a db](https://www.postgresql.org/docs/current/populate.html)
  - [SQL](https://www.postgresql.org/docs/current/sql.html)
  - [SQL syntax - functions](https://www.postgresql.org/docs/current/functions.html)
  - [SQL syntax - $$ notation](https://www.postgresql.org/docs/current/sql-syntax-lexical.html#SQL-SYNTAX-DOLLAR-QUOTING)
  - [transactions](https://www.postgresql.org/docs/current/tutorial-transactions.html)
  - [server config](https://www.postgresql.org/docs/current/runtime-config.html)
  - [PL/pgSQL](https://www.postgresql.org/docs/current/plpgsql.html)
  - [PL/pgSQL - transactions](https://www.postgresql.org/docs/current/plpgsql-transactions.html)
  - [PL/pgSQL - errors](https://www.postgresql.org/docs/current/plpgsql-errors-and-messages.html)
  - [PL/Python](https://www.postgresql.org/docs/current/plpython-funcs.html)