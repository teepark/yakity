#!/usr/bin/env python
# vim: fileencoding=utf8:et:sta:ai:sw=4:ts=4:sts=4

import functools
import logging
import os
import sys

from feather import wsgi
from yakity import configs, client, wsgi_api

jqpath = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'jquery.js')
jquery = open(jqpath, 'r').read()


def app(conf, environ, start_response):
    if environ['PATH_INFO'] in ('/', '/index.html'):
        start_response("200 OK", [
            ("Content-Type", "text/html"),
            ("Content-Length", str(len(homepage)))
        ])
        return [homepage]

    if environ['PATH_INFO'] == "/jquery.js":
        start_response("200 OK", [
            ("Content-Type", "text/javascript"),
            ("Content-Length", str(len(jquery)))])
        return [jquery]

    return wsgi_api.WSGIApp(conf)(environ, start_response)


homepage = r"""<doctype html>
<html>
  <head>
    <style type="text/css">
      body {
        font-family: Lucida Console, Monaco, monospace;
      }

      div.screen {
        margin-left: auto;
        margin-right: auto;
        width: 960px;
        border: 1px solid black;
      }

      div#screen1 {
        margin-top: 160px;
      }

      div#screen1 table {
        margin-left: auto;
        margin-right: auto;
      }

      input#screen1submit {
        height: 4em;
      }

      #screen1errors {
        color: red;
        font-weight: bold;
      }

      div#screen2 {
        font-size: 20px;
        display: none;
      }

      div#chatwindow {
        height: 480px;
        margin-top: 40px;
        overflow: auto;
      }

      div#chatinput {
        margin-left: auto;
        margin-right: auto;
        margin-top: 20px;
        width: 960px;
        border: 1px solid black;
      }

      div#chatinput input {
        width: 100%;
        border: 0;
        color: gray;
        font-size: inherit;
        font-family: inherit;
      }

      form#typingform {
        margin: 0;
        padding: 0;
      }
    </style>
  </head>

  <body>
    <div class="screen" id="screen1">
      <form id="screen1form">
        <table>
          <tr>
            <td>user name:</td>
            <td><input type="text" id="username" tabindex=1></input></td>
            <td rowspan=2><input type="submit" id="screen1submit" value="Join" tabindex=3></input></td>
          </tr><tr>
            <td>room name:</td>
            <td><input type="text" id="roomname" tabindex=2></input></td>
          </tr><tr>
            <td colspan=3 id="screen1errors"></td>
          </tr>
        </table>
      </form>
    </div>

    <div id="screen2">
      <div class="screen" id="chatwindow"></div>
      <div id="chatinput"><form id="typingform"><input type="text" value="type here"></input></form></div>
    </div>

    <script type="text/javascript" src="/jquery.js"></script>
    <script type="text/javascript">
        $(function() {
          var latest = 0;
          var inflight = null;

          var screen1 = $("div#screen1");
          var screen2 = $("div#screen2");
          var usernamebox = $("input#username");
          var roomnamebox = $("input#roomname");
          var screen1form = $("form#screen1form");
          var screen1errors = $("#screen1errors");
          var chatwindow = $("div#chatwindow");
          var chatinputdiv = $("div#chatinput");
          var chatinput = $("div#chatinput input");
          var typingform = $("form#typingform");

          function insertRoomAction(action) {
            var item = $("<div>");

            switch(action.event) {
              case 'join':
                item.text("* " + action.username + " has joined");
                item.css({'color': 'gray'});
                break;
              case 'depart':
                item.text("* " + action.username + " has left");
                item.css({'color': 'gray'});
                break;
              case 'msg':
                item.text(action.username + ": " + action.msg);
            }

            chatwindow.append(item);
            chatwindow.scrollTop(chatwindow[0].scrollHeight);
          };

          function startPull() {
            inflight = $.ajax({
              url: "/" + roomnamebox.val(),
              data: {'last': latest},
              username: usernamebox.val(),
              password: '',
              dataType: 'json',
              type: 'GET',

              success: function(data, status, jqXHR) {
                if (data.length)
                  latest = Math.max(latest, data[data.length - 1].counter);

                startPull();

                for (var i = 0; i < data.length; ++i)
                  insertRoomAction(data[i]);
              },

              error: function(jqXHR, status, exception) {
                if (status === "abort")
                  return;

                if (status === "timeout")
                  startPull();

                if (exception)
                  throw exception;
              }
            });
          };

          screen1form.live("submit", function(event) {
            event.preventDefault();

            startPull();

            $.ajax({
              url: "/" + roomnamebox.val() + "/join",
              username: usernamebox.val(),
              password: '',
              dataType: 'json',

              success: function(data, status, jqXHR) {
                screen1.css({'display': 'none'});
                screen2.css({'display': 'block'});
              },

              error: function(jqXHR, status, exception) {
                screen1errors.text(status + ": " + exception);
                if (exception !== undefined)
                  throw exception;
              }
            });
          });

          chatinput
            .live("focus", function() {
              if (chatinput.val() === 'type here')
                chatinput.val('');
              chatinput.css({'color': 'black'});
            })
            .live("blur", function() {
              chatinput.css({'color': 'gray'});
              if (chatinput.val() === '')
                chatinput.val('type here');
            });

          typingform.live("submit", function(event) {
            event.preventDefault();

            $.ajax({
              url: "/" + roomnamebox.val() + "/",
              data: chatinput.val(),
              processData: false,
              dataType: 'json',
              contentType: 'application/json',
              type: 'POST'
            });

            chatinput.val('');
          });

          $(window).bind('unload', function() {
            $.ajax({
              url: "/" + roomnamebox.val() + "/depart",
              username: usernamebox.val(),
              password: '',
              dataType: 'json',
              async: false
            });
          });
        });
    </script>
  </body>
</html>
"""


def main(environ, argv):
    conf = configs.get_configs("yakity.conf")

    # enable both access and error logging, and print it to stdout
    logging.getLogger('feather').setLevel(logging.INFO)
    logging.getLogger('feather').addHandler(logging.StreamHandler())

    wsgi.serve(("localhost", 8989),
            functools.partial(app, conf),
            worker_count=1)


if __name__ == '__main__':
    sys.exit(main(os.environ, sys.argv))
