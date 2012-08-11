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
    cursor.execute("select id from mails where address = ?", [address])
    result = cursor.fetchone()
    if not result:
        cursor.execute("insert into mails (address) values (?)", [address])
        id = cursor.lastrowid
    else:
        id = result[0]
    cursor.close()
    return id

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
    cursor.execute("insert into articles (from_id, subject, date, message_id) values (?, ?, ?, ?)", [from_id, subject, date, message_id])
    article_id = cursor.lastrowid
    cursor.close()

    if not mail.get('In-Reply-To'):
        top_id = article_id
    else:
        cursor = db_con.cursor()
        cursor.execute("select id from articles where message_id = ?", [mail.get('In-Reply-To')])
        result = cursor.fetchone()
        if not result:
            top_id = article_id
        else:
            top_id = result[0]
        cursor.close()
    db_con.execute("update articles set top_id = ? where id = ?", [top_id, article_id])

    recipients = mail.get('To') + ',' + mail.get('Cc')
    for i in recipients.split(','):
        mail_id = get_mail_id(db_con, i)
        if mail_id:
            db_con.execute("insert into to_assoc (article_id, mail_id) values (?, ?)", [article_id, mail_id])

    db_con.close()
