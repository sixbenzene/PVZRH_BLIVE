import sqlite3
from datetime import datetime
import os

class SqlControl:
    def __init__(self):
        file_list = os.listdir()
        self.conn = sqlite3.connect('blive_usr.db')
        self.cursor = self.conn.cursor()
        self.create_table()


    def create_table(self):
        create_table_sql = '''
            CREATE TABLE IF NOT EXISTS blive_usr (
                id INTEGER PRIMARY KEY,
                uname TEXT NOT NULL,
                sun INTEGER,
                last_sign_in_date TEXT
            )
            ''' 
        # 执行SQL语句
        self.cursor.execute(create_table_sql)
        # 提交事务
        self.conn.commit()    

    def show_tables(self): #显示表
        self.cursor.execute("SELECT * FROM blive_usr")
        rows = self.cursor.fetchall()
        # print(rows)
        # return rows
        for row in rows:
            print(row)
            # break
    def search_usr(self,uname:str): #查找用户
        self.cursor.execute("SELECT sun FROM blive_usr WHERE uname = ?", (uname,))
        result = self.cursor.fetchone()
        if result:
            return result[0]
        else:
            self.insert_data(uname,1000)
            return 1000

    def insert_data(self,uname:str,sun:int): #插入值
        self.cursor.execute("INSERT INTO blive_usr (uname, sun) VALUES (?, ?)", (uname, sun))
        self.conn.commit()

    def update_data(self,uname:str,sun:int): # 更新值
        self.cursor.execute("UPDATE blive_usr SET sun = ? WHERE uname = ?", (sun, uname))
        self.conn.commit()

    def delet_data(self,uname:str): # 删除用户
        self.cursor.execute("DELETE FROM blive_usr WHERE uname = ?", (uname,))
        self.conn.commit()

    def sign_in(self,uname:str): # 签到
        # 获取当前日期
        today = datetime.now().strftime("%Y-%m-%d")
        # print(today)
        # 查询该用户的最后签到日期
        self.cursor.execute("SELECT last_sign_in_date FROM blive_usr WHERE uname = ?", (uname,))
        result = self.cursor.fetchone()

        if result:
            last_sign_in_date = result[0]
            if last_sign_in_date == today:
                return False
            else:
                self.cursor.execute("UPDATE blive_usr SET last_sign_in_date = ? WHERE uname = ?", (today, uname))
                remain_sun = self.search_usr(uname)
                self.update_data(uname,remain_sun+1000)
                self.conn.commit()
                return True
        else:
            self.cursor.execute("INSERT INTO blive_usr (uname, sun,last_sign_in_date) VALUES (?, ?,?)", (uname,2000, today))
            self.conn.commit()
            return True
        
if __name__ == "__main__":
    usr_base = SqlControl()
    # usr_base.create_table()
    # usr_base.delet_data("你好")
    # usr_base.sign_in("你好")
    print(usr_base.search_usr("清哥想要成为技术大佬"))
    # print(usr_base.search_usr("锡不嘻嘻"))
    usr_base.show_tables()

    