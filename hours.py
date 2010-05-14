#!/usr/bin/env python
#
# Copyright 2009 Facebook
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import functools
import datetime
import time
import os.path
import re
import tornado.web
import tornado.wsgi
import unicodedata
import wsgiref.handlers

from google.appengine.api import users
from google.appengine.ext import db

class Entry(db.Model):
    DAYS = ['M','T','W','H','F','S','S']
    
    """A single time entry."""
    user = db.UserProperty(required=True, indexed=True)
    date = db.DateProperty(required=True, indexed=True)
    minutes = db.IntegerProperty()
    updated = db.DateTimeProperty(auto_now=True)
    
    @property
    def weekday(self):
        return self.DAYS[self.date.weekday()]
    
    @property
    def hours(self):
        if self.minutes and self.minutes > 0:
            return self.minutes / 60.0
        else:
            return ''
    
    @property
    def is_today(self):
        if datetime.date.today() == self.date:
            return 'today'
        else:
            return ''


class BaseHandler(tornado.web.RequestHandler):
    """Implements Google Accounts authentication methods."""
    def get_current_user(self):
        user = users.get_current_user()
        if user: user.administrator = users.is_current_user_admin()
        return user

    def get_login_url(self):
        return users.create_login_url(self.request.uri)

    def render_string(self, template_name, **kwargs):
        # Let the templates access the users module to generate login URLs
        return tornado.web.RequestHandler.render_string(
            self, template_name, users=users, **kwargs)


def date_range(period):
    return [ datetime.date(2010, period, d) for d in xrange(1,16)]

class HomeHandler(BaseHandler):
    def get(self):
        dates = date_range(5)
        
        # load all entries for the current period
        q = Entry.all()
        q.filter("user = ", users.get_current_user())
        q.filter("date >=", dates[0])
        q.filter("date <=", dates[-1])
        current_entries = q.fetch(20)
        
        # create empty entries for the dates that don't have entries
        all_entries = []
        for day in dates:
            entry = [e for e in current_entries if e.date == day]
            if len(entry) == 0:
                all_entries.append(Entry(date=day, user=users.get_current_user()))
            else:
                all_entries.append(entry[0])
        
        self.render("home.html", entries=all_entries)
        
    def post(self):
        entry_date = datetime.date(*[int(d) for d in self.get_argument("date").split('-')])
        entry = Entry.all().filter("user =", users.get_current_user()).filter("date =", entry_date).get()
        hours = self.get_argument("hours", "")
        
        if hours == '' or hours == '0':
            if entry:
                entry.delete()
        else:
            minutes = int(float(hours) * 60)
            if not entry:
                entry = Entry(date=entry_date, user=users.get_current_user())
            entry.minutes = minutes
            entry.put()
        self.redirect("/")
        


class ReportHandler(BaseHandler):
    def get(self):
        if not self.current_user.administrator:
            raise tornado.web.HTTPError(403)
        
        dates = date_range(5)
        
        # load all entries for the current period
        q = Entry.all()
        q.filter("date >=", dates[0])
        q.filter("date <=", dates[-1])
        q.order("date")
        current_entries = q.fetch(1000)
        
        user_list = {}
        for entry in current_entries:
            username = entry.user.nickname()
            if not user_list.has_key(username):
                user_list[username] = []
            user_list[username].append(entry)
        
        blank_entries = [Entry(date=d, user=self.get_current_user()) for d in dates]
        self.render("report.html", user_list=user_list, blank_entries=blank_entries)

settings = {
    "template_path": os.path.join(os.path.dirname(__file__), "templates"),
    "xsrf_cookies": True,
}

application = tornado.wsgi.WSGIApplication([
    (r"/", HomeHandler),
    (r"/admin", ReportHandler),
], **settings)


def main():
    os.environ["TZ"]="US/Pacific"
    time.tzset()
    wsgiref.handlers.CGIHandler().run(application)


if __name__ == "__main__":
    main()
