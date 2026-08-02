This file describes all steps of execution for THM room (Pickle Rick)
Difficulty - Easy

Target IP: http://10.113.147.200

A scan was performed using nmap:

` sudo nmap -T4 -p- -oN nmap.txt 10.113.147.200 `

The scan showed a web server running on port 80.

I opened the website:

` http://10.113.147.200 `

The page title was:

"Rick is sup4r cool"

The website itself did not reveal much, except in the page source code
there was a comment with the user name -> "R1ckRul3s" 
then I started directory enumeration.

I used gobuster:

` gobuster dir -u http://10.113.147.200 -w /usr/share/wordlists/dirb/common.txt `

A few directories were found, including:

/assets/
/portal.php
/robots.txt
(and more which were not accessible)

The /assets/ directory contained normal website resources.

The interesting discovery was:

` http://10.113.147.200/portal.php `

Opening portal.php showed a login page.

After checking robots.txt:

` http://10.113.147.200/robots.txt `

The file contained:

Wubbalubbadubdub

I tried it as the password and it actually worked

Login credentials:

Username: R1ckRul3s
Password: Wubbalubbadubdub

After logging in, I was presented with a bunch of tabs which I couldn't 
access except the first one which was in-built command execution panel.

I tested the command execution with:

` whoami `

The result:

www-data

The server was running commands as the web user.

I started exploring the web directory:

` ls -la /var/www/html `

Found:

/var/www/html/
    Sup3rS3cretPickl3Ingred.txt
    clue.txt
    denied.php
    index.html
    login.php
    portal.php
    robots.txt
    assets/


Reading Sup3rS3cretPickl3Ingred.txt:

` less /var/www/html/Sup3rS3cretPickl3Ingred.txt `

(NOTE: I used less instead of cat, because I didn't have right access)

#1 FLAG FOUND / ingredient:
<details>
<summary>Spoiler Alert!</summary>

mr. meeseek hair

</details>

Reading clue.txt:

` less /var/www/html/clue.txt `

Content:

"look around the file system for the other ingredients"

Decided to filter the filesystem to speed-up my search and I relied on
some keywords that could be helpful. So I used this command

` find / -iname "*ingredient*" 2>/dev/null `

I Found this directory:

/home/rick/second ingredients

Reading the file:

` less "/home/rick/second ingredients" `

#2 FLAG FOUND / ingredient:
<details>
<summary>Spoiler Alert!</summary>

jerry tear

</details>

While checking the website source, I found another hidden comment:

<!-- Vm1wR1UxTnRWa2RUV0d4VFlrZFNjRlV3V2t0alJsWnlWbXQwVkUxV1duaFZNakExVkcxS1NHVkliRmhoTVhCb1ZsWmFWMVpWTVVWaGVqQT0= -->

The string was Base64 encoded multiple times.

Tried to decode it using in shell:

` echo 'string_here' | base64 -d | base64 -d | base64 -d ... `

Final output:

RABBIT HOLE

(This was only a distraction and did not lead anywhere.)

I decided to check for privilege escalation paths.

Used:

` sudo -l `

Output:
User www-data may run the following commands:
(ALL) NOPASSWD: ALL

This means www-data can execute commands as root without a password.

Because the command panel did not provide a persistent shell, root commands can be executed directly using sudo.

Example:
` sudo whoami `

Output:
root

Root access was always there. No escalating privileges needed.

So I started checking for root directories

` sudo ls -la /root `

and decided to filter search for remaining flags:

` sudo find / -name "*.txt" 2>/dev/null `

This is where I got a file named 3rd.txt
#3 FLAG FOUND / ingredient:
<details>
<summary>Spoiler Alert!</summary>

fleeb juice

</details>


Room completed.
