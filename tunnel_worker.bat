@echo off
ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=NUL -o ServerAliveInterval=60 -o ServerAliveCountMax=3 -R 80:localhost:5000 localhost.run > "%~dp0logs\tunnel.log" 2>&1
