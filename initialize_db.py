#!/usr/bin/python3
import sqlite3


def main():
    conn = sqlite3.connect("repos.db")
    c = conn.cursor()
    # create table
    c.execute("""CREATE TABLE IF NOt EXISTS repos(
                id INTEGER PRIMARY KEY ASC ON CONFLICT IGNORE, 
                url TEXT, stars INTEGER, checked INTEGER DEFAULT 0)""")
    # index number of stars
    c.execute("""CREATE INDEX index_stars ON repos(stars)""")
    # save the changes
    conn.commit()
    c.close()
    conn.close()
    return


if __name__ == '__main__':
    main()
