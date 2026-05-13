# Conference Management App - README

## What is this

This is a python app that manages conference data. It uses two databases:
- MySQL (appdbproj) - stores all the conference info like attendees, sessions, companies, rooms
- Neo4j - stores connections between attendees (like a social network)

## What you need before running

1. MySQL 8.0 running with the appdbproj database imported
2. Neo4j running with the attendee data imported
3. Python with mysql-connector-python and neo4j packages installed

## How to set up the databases

### MySQL
Open MySQL 8.0 Command Line, enter password (root), then run:
```
source C:\Users\appDB\Desktop\appdbproj.sql
```

### Neo4j
Open a command prompt and run:
```
cd C:\Users\appDB\Documents\neo4j-community-5.26.19
bin\neo4j console
```
Then go to http://localhost:7474 in a browser, log in (neo4j / neo4jneo4j) and paste in the contents of appdbprojNeo4j.json to create the nodes and relationships.

## How to install the python packages

```
C:\ProgramData\anaconda3\python.exe -m pip install mysql-connector-python neo4j
```

## How to run the app

Open a command prompt and run:
```
cd C:\Users\appDB\Desktop
C:\ProgramData\anaconda3\python.exe main.py
```

## What the menu options do

1 - Lets you search for a speaker by name and shows their sessions and rooms
2 - Enter a company ID and it shows all attendees from that company with their session details
3 - Add a new attendee to the database by entering their ID, name, DOB, gender and company
4 - Enter an attendee ID and it shows who they are connected to in neo4j
5 - Connect two attendees together in neo4j by entering both their IDs
6 - Shows all the rooms and their capacity
x - Quits the app
