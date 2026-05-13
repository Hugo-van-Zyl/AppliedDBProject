# main.py
# conference management app
# uses mysql for the conference data and neo4j for the connections between attendees

import mysql.connector
from neo4j import GraphDatabase

# mysql connection
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="root", # my mysql password
    database="appdbproj"
)
cursor = db.cursor() # this runs the sql side

neo4j_driver = GraphDatabase.driver( # neo4j connection
    "bolt://localhost:7687",
    auth=("neo4j", "neo4jneo4j") # neo4j login
)

rooms = None # stores rooms so it doesnt keep reloading

# main loop keeps going until user types x
while True:
    # print menu
    print("\nConference Management")
    print("---------------------")
    print("")
    print("MENU")
    print("====")
    print("1 - View Speakers & Sessions")
    print("2 - View Attendees by Company")
    print("3 - Add New Attendee")
    print("4 - View Connected Attendees")
    print("5 - Add Attendee Connection")
    print("6 - View Rooms")
    print("x - Exit application")
    choice = input("Choice: ") # get users choice

    # option 1 - search for speakers
    if choice == "1":
        name = input("\nEnter speaker name : ") # get speaker name or part of it

        # join session and room tables so i can get the room name too
        # LIKE with % lets me do partial matching on the name
        cursor.execute("SELECT s.speakerName, s.sessionTitle, r.roomName FROM session s JOIN room r ON s.roomID = r.roomID WHERE s.speakerName LIKE %s", ("%" + name + "%",))
        results = cursor.fetchall() # gets all matching rows

        print("Session Details For : ", name)
        print("---------------------------------------------")
        if len(results) == 0: # nothing came back
            print("No speakers found of that name")
        else:
            for row in results:
                print(row[0], " | ", row[1], " | ", row[2]) # speaker | session | room

    # option 2
    elif choice == "2":
        while True: # keep asking until valid input
            companyID = input("\nEnter Company ID : ")
            # has to be a number and greater than 0
            try:
                companyID = int(companyID)
                if companyID <= 0:
                    continue
            except ValueError:
                continue # typed letters or something

            # check company exists
            cursor.execute("SELECT companyName FROM company WHERE companyID = %s", (companyID,))
            company = cursor.fetchone() # only expecting one row

            if company is None: # doesnt exist
                print("Company with ID ", companyID, " doesn't exist")
                continue

            companyName = company[0] # name is first column
            print(companyName, " Attendees")

            # big join to get attendee info with their session and room details
            # links attendee -> registration -> session -> room using their IDs
            cursor.execute("""SELECT a.attendeeName, a.attendeeDOB, s.sessionTitle, s.speakerName, s.sessionDate, r.roomName
                FROM attendee a
                JOIN registration reg ON a.attendeeID = reg.attendeeID
                JOIN session s ON reg.sessionID = s.sessionID
                JOIN room r ON s.roomID = r.roomID
                WHERE a.attendeeCompanyID = %s""", (companyID,))
            results = cursor.fetchall()

            if len(results) == 0:
                print("No attendees found for ", companyName) # exists but no one registered
                continue
            else:
                for row in results: # print each row
                    print(row[0], " | ", row[1], " | ", row[2], " | ", row[3], " | ", row[4], " | ", row[5])
                break # back to menu

    # option 3 - add new attendee
    elif choice == "3":
        print("\nAdd New Attendee")
        print("----------------")
        attID = input("Attendee ID : ")
        name = input("Name : ")
        dob = input("DOB : ")
        gender = input("Gender : ")
        compID = input("Company ID : ")

        # capitalize makes "male" into "Male" so it matches either way
        if gender.capitalize() != "Male" and gender.capitalize() != "Female":
            print("*** ERROR *** Gender must be Male/Female")
        else:
            try:
                compIDint = int(compID)
                cursor.execute("SELECT companyID FROM company WHERE companyID = %s", (compIDint,)) # check company exists
                compResult = cursor.fetchone()
                if compResult is None:
                    print("*** ERROR *** Company ID:", compID, "does not exist")
                else:
                    # try insert the new attendee
                    try:
                        cursor.execute("INSERT INTO attendee (attendeeID, attendeeName, attendeeDOB, attendeeGender, attendeeCompanyID) VALUES (%s, %s, %s, %s, %s)",
                            (attID, name, dob, gender.capitalize(), compID))
                        db.commit() # wont save without this
                        print("Attendee successfully added")
                    except mysql.connector.IntegrityError as ie:
                        # happens when the ID is already taken
                        #print(ie) # was using this to debug
                        print("*** ERROR *** Attendee ID:", attID, "already exists")
                    except mysql.connector.Error as e:
                        print("*** ERROR ***", e) # wrong date format or something
            except ValueError:
                print("*** ERROR *** Company ID:", compID, "does not exist")

    # option 4 - show connected attendees from neo4j
    elif choice == "4":
        while True:
            attID = input("\nEnter Attendee ID : ")
            try:
                attID = int(attID)
            except ValueError:
                print("*** ERROR *** Invalid attendee ID")
                continue

            cursor.execute("SELECT attendeeName FROM attendee WHERE attendeeID = %s", (attID,)) # check mysql first
            result = cursor.fetchone()

            if result is None: # not in mysql
                print("*** ERROR *** Attendee does not exist")
                continue

            attendeeName = result[0]
            print("Attendee Name: ", attendeeName)
            print("---------------------")

            # go to neo4j and find connections
            # using - not -> cos direction not importan
            with neo4j_driver.session(database="neo4j") as neo_session:
                neo_result = neo_session.run(
                    "MATCH (a:Attendee {AttendeeID: $id})-[:CONNECTED_TO]-(b:Attendee) RETURN b.AttendeeID AS connID",
                    id=attID
                )
                connections = [] # put the connected ids in here
                for record in neo_result:
                    connections.append(record["connID"])

            if len(connections) == 0:
                print("No connections")
            else:
                print("These attendees are connected:")
                for cid in connections:
                    cursor.execute("SELECT attendeeName FROM attendee WHERE attendeeID = %s", (cid,)) # get name from mysql
                    n = cursor.fetchone()
                    if n is not None:
                        print(cid, " | ", n[0])

            break

    # option 5 - connect two attendees
    elif choice == "5":
        while True:
            id1 = input("\nEnter Attendee 1 ID : ")
            id2 = input("Enter Attendee 2 ID : ")

            try: # both have to be numbers
                id1 = int(id1)
                id2 = int(id2)
            except ValueError:
                print("*** ERROR *** Attendee IDs must be numbers")
                continue

            if id1 == id2: # same person
                print("*** ERROR *** An attendee cannot connect to him/herself")
                continue

            # check both exist in mysql first
            cursor.execute("SELECT attendeeID FROM attendee WHERE attendeeID = %s", (id1,))
            check1 = cursor.fetchone()
            cursor.execute("SELECT attendeeID FROM attendee WHERE attendeeID = %s", (id2,))
            check2 = cursor.fetchone()

            if check1 is None or check2 is None:
                print("*** ERROR *** One or both attendee IDs do not exist")
                continue

            # check if already connected
            with neo4j_driver.session(database="neo4j") as neo_session:
                neo_result = neo_session.run(
                    "MATCH (a:Attendee {AttendeeID: $id1})-[:CONNECTED_TO]-(b:Attendee {AttendeeID: $id2}) RETURN COUNT(*) AS cnt",
                    id1=id1, id2=id2
                )
                cnt = neo_result.single()["cnt"] # gets the count

            if cnt > 0:
                print("*** ERROR *** These attendees are already connected")
                continue

            # merge makes nodes if they dont already exists, then create adds the relationship
            with neo4j_driver.session(database="neo4j") as neo_session:
                neo_session.run(
                    "MERGE (a:Attendee {AttendeeID: $id1}) MERGE (b:Attendee {AttendeeID: $id2}) CREATE (a)-[:CONNECTED_TO]->(b)",
                    id1=id1, id2=id2
                )

            print("Attendee", id1, "is now connected to Attendee", id2)
            break

    # option 6 - rooms
    elif choice == "6":
        # only loads once, spec says new rooms wont show until restart
        if rooms is None:
            cursor.execute("SELECT roomID, roomName, capacity FROM room")
            rooms = cursor.fetchall() # save so we dont query again

        print("RoomID", " | ", "RoomName", "          | ", "Capacity")
        for room in rooms:
            print(room[0], "     | ", room[1], "  | ", room[2])

    elif choice == "x": # quit
        print("Goodbye!")
        break

    # anything else just shows menu again

# close connections
cursor.close()
db.close()
neo4j_driver.close()
