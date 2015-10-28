import MySQLdb
import sqlite3


class Db:

    def __init__(self, credentials):
        self.credentials = credentials
        self.conn = MySQLdb.connect(**credentials)
        

    def query(self, sql, params = None):
        curs = self.curs()
        if params is None:
            curs.execute(sql)
        else:
            curs.execute(sql, params)
        
        return curs.fetchall()


    def curs(self):
        return self.conn.cursor()


    def query_dict(self, sql, params = None):
        curs = self.conn.cursor(MySQLdb.cursors.DictCursor)
        if params is None:
            curs.execute(sql)
        else:
            curs.execute(sql, params)
        
        return curs.fetchall()


    def getCredentials(self):
        credentials = self.credentials.copy()
        del credentials['passwd']
        return credentials


    def insert_or_update(self, table_name, data):
        for line in data:
            headers = [key for key,val in sorted(line.items())]
            
            quoted_values = ['"%s"' % (val.replace('"','\\"') if type(val) is str else val) for key,val in sorted(line.items())]
            duplicate_key_clauses = ['%s="%s"' % (key, val.replace('"','\\"') if type(val) is str else val) for key,val in sorted(line.items())]

            sql = """
                INSERT INTO %s
                (%s)
                VALUES (%s)
                ON DUPLICATE KEY UPDATE
                %s
            """ % (table_name, ','.join(headers), ','.join(quoted_values),','.join(duplicate_key_clauses))
            self.query(sql)

class DbLite:

    def __init__(self):
        self.conn = sqlite3.connect("metadata/leagues.db")
        self.conn.row_factory = sqlite3.Row
        

    def query(self, sql):
        curs = self.curs()
        curs.execute(sql)
        
        return curs.fetchall()


    def curs(self):
        return self.conn.cursor()


    def query_dict(self, sql, params = None):
        curs = self.conn.cursor()

        if params is None:
            curs.execute(sql)
        else:
            curs.execute(sql, params)

        
        return [dict(zip(row.keys(), row)) for row in curs.fetchall()]


    def commit(self):
        self.conn.commit()




