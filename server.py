#!/usr/bin/python
# -*- coding: utf-8

from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
import sqlite3
from datetime import datetime, timedelta
import re

class MyHandler(BaseHTTPRequestHandler):
    def __init__(self, req, client, server):
        BaseHTTPRequestHandler.__init__(self, req, client, server)
    def do_GET(self):
        self.conn = sqlite3.connect("data.db")
        reg = re.compile(r'^/(article|file)/(\d+)$')
        m = reg.match(self.path)
        if self.path == "/":
            self.home()
        elif m and m.group(1) == "article":
            self.article(int(m.group(2)))
        elif m and m.group(1) == "file":
            self.showfile(int(m.group(2)))
        else:
            self.send_error(404)
        self.conn.close()
    def article(self, artid):
        c = self.conn.cursor()
        c.execute("SELECT subject FROM articles WHERE id = ?", (artid,))
        (subject,) = c.fetchone()
        c.close()
        self.send_response(200)
        self.end_headers()
        self.common_header(("%s - ぃぬ速" % subject.encode('utf-8')).encode('utf-8'))
        self.wfile.write("<pre>")
        with open("article/%d" % artid) as f:
            self.wfile.write(f.read())
        self.wfile.write("</pre>")
        self.common_footer()
    def showfile(self, fid):
        c = self.conn.cursor()
        c.execute("SELECT path FROM files WHERE id = ?", (fid,))
        (path,) = c.fetchone()
        self.send_response(200)
        self.end_headers()
        self.common_header("%s - ぃぬ速" % path)
        self.wfile.write("<ul>")
        for (subject, msgid) in c.execute("SELECT subject,articles.message_id FROM articles, file_assoc WHERE file_assoc.file_id = ? ORDER BY date DESC", (fid,)):
            self.wfile.write("<li><a href=\"http://thread.gmane.org/%s\">%s</a></li>" % (msgid[1:][:-1], subject))
        self.wfile.write("</ul>")
        c.close()
        self.common_footer()
    def home(self):
        self.send_response(200)
        self.end_headers()
        self.common_header("ぃぬ速")
        self.hottest_topics()
        self.hottest_files()
        # self.fxxking_topics()
        self.common_footer()
    def common_header(self,title):
        self.wfile.write("""
<html>
<head>
<title>%s</title>
</head>
<body>
                         """ % (title))
    def common_footer(self):
        self.wfile.write("""
</body>
</html>
""")
    def hottest_topics(self):
        self.wfile.write("<h2>Hottest Topics</h2>")
        self.wfile.write("<div class=\"topic\" id=\"hot-topics\">")
        self.wfile.write("<ul>")
        t = datetime.now()+timedelta(days=-7)
        date = t.strftime("%Y-%m-%d %H:%M:%S")
        c = self.conn.cursor()
        for (msgid, subject) in c.execute("SELECT articles.message_id, articles.subject FROM articles,(SELECT top_id,count(*) AS cnt FROM articles WHERE date > ? GROUP BY top_id ORDER BY cnt DESC LIMIT 10) AS a WHERE articles.id = a.top_id", (date,)):
            self.wfile.write("<li><a href=\"http://thread.gmane.org/%s\">%s</a></li>" % (msgid[1:][:-1], subject))
        self.wfile.write("</ul>")
        self.wfile.write("</div>")
        c.close()
    def hottest_files(self):
        self.wfile.write("<h2>Hottest Files</h2>")
        self.wfile.write("<div class=\"topic\" id=\"hot-files\">")
        self.wfile.write("<ul>")
        t = datetime.now()+timedelta(days=-7)
        date = t.strftime("%Y-%m-%d %H:%M:%S")
        c = self.conn.cursor()
        for (fid, subject) in c.execute("SELECT files.id, files.path FROM files, (SELECT file_id, COUNT(*) AS cnt FROM (SELECT file_id FROM file_assoc, articles WHERE date > ? AND article_id = id) AS a GROUP BY file_id ORDER BY cnt DESC LIMIT 10) AS b WHERE files.id = b.file_id", (date,)):
            self.wfile.write("<li><a href=\"/file/%d\">%s</a></li>" % (fid, subject))
        self.wfile.write("</ul>")
        self.wfile.write("</div>")
        c.close()
    def fxxking_topics(self):
        self.wfile.write("<h2>Fxxking Topics</h2>")
        self.wfile.write("<div class=\"topic\" id=\"fxxk-topic\">")
        self.wfile.write("</div>")

# localの3000でサーバを動かす
def run(server_class=HTTPServer,
        handler_class=BaseHTTPRequestHandler):
    server_address = ('', 3000)
    httpd = server_class(server_address, handler_class)
    httpd.serve_forever()

if __name__ == '__main__':
    run(HTTPServer, MyHandler)
