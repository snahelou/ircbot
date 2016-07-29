import sys
import socket
import string
import time 
import subprocess
import select
import os
from multiprocessing import Process, Pipe

HOST="54.171.171.138"
PORT=6667

channel_list=['#btwin','#citadelle','#euratec','#campus','#heron','#seb','#pierre']

NICK="Sacha"
IDENT="sacha"
REALNAME="SachaBot"

def process_connection(s):
  readbuffer=""

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

  while 1:
    if p.poll(1):
      # New line type "Pop fantominus a http://www.google.fr;SebAndro;xxxx"
      # message;user1;user2
      txt = f.stdout.readline().split(';')
      message=txt[0] 
      s.send('PRIVMSG ' + channel + ' : ' + message +'\r\n')
      txt.pop(0)
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


