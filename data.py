#!/usr/bin/env python
import os
import re
import sys
import sqlite3
import email.parser
import email.utils

def usage():
    sys.exit()

def get_mail_id(db_con, address):
    address = email.utils.parseaddr(address)[1]
    if not re.match(r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,4}$', address):
        return

    cursor = db_con.cursor()
    cursor.execute("select id from mails where address = ?", (address,))
    result = cursor.fetchone()
    if not result:
        cursor.execute("insert into mails (address) values (?)", (address,))
        id = cursor.lastrowid
    else:
        id = result[0]
    cursor.close()
    return id

def get_file_ids(db_con, path):
    cursor = db_con.cursor()
    file_ids = []

    directory = path.split('/')
    for i in range(1, len(directory) + 1):
        path = '/'.join(directory[:i])
        cursor.execute("select id from files where path = ?", (path,))
        result = cursor.fetchone()
        if not result:
            cursor.execute("insert into files (path) values (?)", (path,))
            file_ids.append(cursor.lastrowid)
        else:
            file_ids.append(result[0])

    cursor.close()
    return file_ids

if __name__ == '__main__':
    
    if len(sys.argv) < 3:
        usage()

    try:
        db_con = sqlite3.connect(sys.argv[1], isolation_level=None)
    except IOError:
        sys.stderr.write('Failed to open db file: %s\n' % (sys.argv[1]))
        usage()

    try:
        f = open(sys.argv[2])
    except IOError:
        sys.stderr.write('Failed to open email file: %s\n' % (sys.argv[2]))
        usage()

    parser = email.parser.Parser()
    mail = parser.parse(f)
    
    from_id = get_mail_id(db_con, mail.get('From'))
    subject = mail.get('Subject')
    date = '%04d/%02d/%02d %02d:%02d:%02d' % email.utils.parsedate(mail.get('Date'))[:-3]
    message_id = mail.get('Message-ID')

    cursor = db_con.cursor()
    cursor.execute("insert into articles (from_id, subject, date, message_id) values (?, ?, ?, ?)", (from_id, subject, date, message_id))
    article_id = cursor.lastrowid
    cursor.close()

    if not mail.get('In-Reply-To'):
        top_id = article_id
    else:
        cursor = db_con.cursor()
        cursor.execute("select id from articles where message_id = ?", (mail.get('In-Reply-To'),))
        result = cursor.fetchone()
        if not result:
            top_id = article_id
        else:
            top_id = result[0]
        cursor.close()
    db_con.execute("update articles set top_id = ? where id = ?", (top_id, article_id))

    recipients = mail.get('To') + ',' + mail.get('Cc')
    for i in recipients.split(','):
        mail_id = get_mail_id(db_con, i)
        if mail_id:
            db_con.execute("insert into to_assoc (article_id, mail_id) values (?, ?)", (article_id, mail_id))

    body = mail.get_payload()
    begin = body.find('\n---\n')
    if begin:
        file_ids = []
        diff = body[begin+5:]
        regex = re.compile(r'^diff --git a/\S* b/(\S*)')
        for i in diff.split('\n'):
            match = regex.match(i)
            if match:
                file_ids += get_file_ids(db_con, match.group(1))
        for file_id in set(file_ids):
            db_con.execute("insert into file_assoc (article_id, file_id) values (?, ?)" , (article_id, file_id))

    db_con.close()
