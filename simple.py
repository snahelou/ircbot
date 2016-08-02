import sys
import json

import socket
import string
import time 
import subprocess
import select
import os
from multiprocessing import Process, Pipe

HOST="your irc host"
PORT=6667

channel_list=['#btwin','#citadelle','#euratec','#heron']
register_list={
  '#btwin'     : [],
  '#citadelle' : [],
  '#euratec'   : [],
  '#heron'     : [],
}

NICK="Sacha"
IDENT="sacha"
REALNAME="SachaBot"

def process_connection(s):
  readbuffer=""
  BOOT=0

  while 1:
    try:
      msg = s.recv(4096)
      readbuffer=readbuffer+msg
      temp=string.split(readbuffer, "\n")
      readbuffer=temp.pop( )
      print temp
      for line in temp:
       line=string.rstrip(line)
       line=string.split(line)

       if(line[0]=="PING"):
         s.send("PONG %s\r\n" % line[1])

       file='/tmp/notify'
       if BOOT == 0:
         BOOT = 1
         with open(file, 'r') as fi:
           try:
             register_list = json.load(fi)
             # if the file is empty the ValueError will be thrown
           except ValueError:
            register_list = {}

       if ( len(line) > 3 ) and (line[3][1:] == "Register"):
         register_list[line[2]].append(line[0].split('!')[0][1:])
         print register_list
         with open(file, 'w') as fi:
             data = json.dump(register_list,fi)
         
       if ( len(line) > 3 ) and (line[3][1:] == "Leave"):
         register_list[line[2]].remove(line[0].split('!')[0][1:])
         print register_list
         with open(file, 'w') as fi:
             data = json.dump(register_list,fi)

       if ( len(line) > 3 ) and (line[1] == "QUIT"):
         #register_list[line[2]].remove(line[0].split('!')[0][1:])
         for a in register_list.itervalues():
           try:
             a.remove(line[0].split('!')[0][1:])
           except ValueError:
             pass
         print register_list
         with open(file, 'w') as fi:
             data = json.dump(register_list,fi)

       if ( len(line) > 3 ) and (line[1] == "PART"):
         register_list[line[2]].remove(line[0].split('!')[0][1:])
         print register_list
         with open(file, 'w') as fi:
             data = json.dump(register_list,fi)
    except socket.error:
      # Permet d avoir un recv non bloquant, sinon on doit attendre un message....
      print "No response from server"
      time.sleep(1)



def process_channel(channel,s):
  print "I WILL PROCESS "+channel+ " using /tmp/" + channel[1:]
  f = subprocess.Popen(['tail','-F','-n','0','/tmp/'+channel[1:]],\
  stdout=subprocess.PIPE,stderr=subprocess.PIPE)
  p = select.poll()
  p.register(f.stdout)

  s.send("JOIN "+channel +"\r\n")
  file = '/tmp/notify'
  with open(file, 'r') as fi:
    try:
        register_list = json.load(fi)
    # if the file is empty the ValueError will be thrown
    except ValueError:
        register_list = {}
  while 1:
    if p.poll(1):
      # New line type "Pop fantominus a http://www.google.fr;SebAndro;xxxx"
      # message;user1;user2
      txt = f.stdout.readline().split(';')
      message=txt[0] 
      print txt 
      s.send('PRIVMSG ' + channel + ' : ' + message +'\r\n')
      txt.pop(0)
      txt = txt + register_list[channel]
      print channel
      print register_list
      print register_list[channel]
      for i in range(len(txt)):
        print "jenvoie a "+ txt[i].rstrip('\r\n')
        s.send('PRIVMSG ' + txt[i].rstrip('\r\n') + ' : ' + message +'\r\n')
      time.sleep(1)



if __name__ == '__main__':
  jobs = []

  s=socket.socket( )
  s.settimeout(3.0)
  s.connect((HOST, PORT))
  s.send("NICK %s\r\n" % NICK)
  s.send("USER %s %s bla :%s\r\n" % (IDENT, HOST, REALNAME))

  #Thread main de connection
  p = Process(target=process_connection, args=(s,))
  jobs.append(p)
  p.start()
  
  #On sleep 5s le temps de la connection
  time.sleep(5)

  #On lance le join des bots sur les channels
  for i in xrange(0,len(channel_list)):
    print "Start %d" % i
    p = Process(target=process_channel, args=(channel_list[i],s,))
    jobs.append(p)
    p.start()
    # sleep for no ban :D
    time.sleep(2)

  #On wait les fils (qui ne se termineront jamais :D )
  for j in jobs:
    j.join()


