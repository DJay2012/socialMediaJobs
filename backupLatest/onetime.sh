#!/bin/bash


     # Run the scripts
#/usr/bin/python3 /home/fedora/jobs/socialmediafeeds/MainScriptXfeed.py  
#sleep 60
/usr/bin/python3 /home/fedora/jobs/socialmediafeeds/MainapifyFacebook.py 
sleep 60
/usr/bin/python3 /home/fedora/jobs/socialmediafeeds/MainScriptYoutubeAll.py 
sleep 60
/usr/bin/python3 /home/fedora/jobs/socialmediafeeds/MainScriptyoutube.py 
sleep 60
/usr/bin/python3 /home/fedora/jobs/socialmediafeeds/mongodbtocollectionpnqxfeed.py 
sleep 60
/usr/bin/python3 /home/fedora/jobs/socialmediafeeds/mongodbtocollectionpnqyoutube.py 
sleep 60
/usr/bin/python3 /home/fedora/jobs/socialmediafeeds/facebookdatatomongo.py 
