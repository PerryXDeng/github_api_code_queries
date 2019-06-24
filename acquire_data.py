#!/usr/bin/python3
import requests
import time
import sqlite3
import credentials as creds

# for rate limit, 2 seconds per request
INTERVAL:int = 2
QUERY_BATCH_SIZE:int = 30


def http_get(session:requests.Session, url:str):
    response = session.get(url)
    time.sleep(INTERVAL)
    return response


def session_authenticated(session:requests.Session) -> bool:
    # personal access token
    session.auth = (creds.user, creds.token)
    user_info = http_get(session, "https://api.github.com/user")
    return user_info.json()["login"] == creds.user


def ranged_code_query(session:requests.Session, db_conn, substring:str, table_name:str, start:int, end:int):
    num_queries:int = (end - start) // QUERY_BATCH_SIZE
    c = db_conn.cursor()
    for iteration in range(num_queries):
        batch_start = iteration * QUERY_BATCH_SIZE
        batch_end = (iteration + 1) * QUERY_BATCH_SIZE
        if batch_end > end:
            batch_end = end

        items = []
        retrying = True
        while retrying:
            print("\nQuerying Batch %d - %d" % (batch_start, batch_end))
            query_url = 'https://api.github.com/search/code?q="%s"+size:%d..%d' % (substring, batch_start, batch_end)
            response = http_get(session, query_url)
            result_set = response.json()
            try:
                items = result_set["items"]
                retrying = False
            except KeyError:
                # possibly rate limited
                print(result_set)
                retrying = True
                wait_time:int = int(response.headers["Retry-After"])
                print("retrying after %d sec" % wait_time)
                time.sleep(wait_time)

        print("# of Results: %d" % len(items))
        for item in items:
            repo = item["repository"]
            id:int = repo["id"]
            name:str = repo["full_name"]
            num_stars:int = http_get(session, "https://api.github.com/repos/" + name).json()["stargazers_count"]
            sql_query = "INSERT INTO %s(id, url, stars) VALUES (%d, '%s', %d)" % (table_name, id, name, num_stars)
            c.execute(sql_query)
        db_conn.commit()
    c.close()


def main():
    session = requests.Session()
    if not session_authenticated(session):
        print("Authentication Failed")
        exit(1)
    db_conn = sqlite3.connect("repos.db")
    ranged_code_query(session, db_conn, "new+LoginContext", "repos", 1, 3000)
    db_conn.close()


if __name__ == '__main__':
    main()
