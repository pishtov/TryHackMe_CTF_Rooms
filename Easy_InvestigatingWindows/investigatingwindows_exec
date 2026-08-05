# THM - Windows Forensics (Active Directory Investigation)

**Difficulty:** Easy

---

# Initial Access

After starting the virtual machine and connecting to the TryHackMe VPN, I connected to the Windows Active Directory machine using **Remote Desktop Protocol (RDP).**

On my Windows machine I opened **Remote Desktop Connection** by typing:

```text
rdp
```

into the Start Menu search.

After opening the client, I expanded **Show Options** and entered the following information.

**Computer**

```text
<THM Target IP>
```

**Username**

```text
Administrator
```

**Password**

```text
letmein123!
```

After accepting the certificate warning, I was logged into the Windows Server desktop.

---

# Question 1

## What version of Windows is running?

I opened **Windows PowerShell** from the Start Menu.

To enumerate system information:

```powershell
Get-ComputerInfo
```

To display only operating system information:

```powershell
Get-ComputerInfo -Property "Os*"
```

### Answer

```
Windows Server 2016
```

---

# Question 2

## Which user logged in last?

First, I enumerated all local users.

```powershell
Get-LocalUser
```

Then I checked each account's last login.

```powershell
net user Administrator | findstr "Last"
```

The most recent login belonged to:

### Answer

```
Administrator
```

---

# Question 3

## When did John log on last?

Using the following command:

```powershell
net user John | findstr "Last"
```

The output displayed John's last login.

### Answer

```
03/02/2019 5:48:32 PM
```

---

# Question 4

## What IP does the system connect to when it first starts?

I first inspected the Windows hosts file.

```
C:\Windows\System32\drivers\etc\hosts
```

Several suspicious entries redirected domains to local addresses.

Next, I opened the Registry Editor.

```text
regedit
```

Then navigated to:

```
HKEY_LOCAL_MACHINE
└── SOFTWARE
    └── Microsoft
        └── Windows
            └── CurrentVersion
                └── Run
```

Inside the **Run** key I found a suspicious value named:

```
UpdateSvc
```

Inspecting it revealed the IP address contacted at startup.

### Answer

```
10.34.2.3
```

---

# Question 5

## Which two accounts have administrative privileges besides Administrator?

To enumerate the local Administrators group:

```powershell
Get-LocalGroupMember -Group "Administrators"
```

### Answer

```
Jenny, Guest
```

---

# Question 6

## What is the name of the malicious scheduled task?

First, I listed all scheduled tasks.

```powershell
Get-ScheduledTask
```

To reduce the output:

```powershell
Get-ScheduledTask | Where {$_.TaskPath -eq "\"}
```

Among the remaining tasks, one appeared malicious.

### Answer

```
Clean file system
```

---

# Question 7

## What file was the scheduled task configured to execute?

I stored the task in a variable.

```powershell
$task = Get-ScheduledTask | Where TaskName -EQ "Clean file system"
```

Then displayed its configured action.

```powershell
$task.Actions
```

### Answer

```
nc.ps1
```

---

# Question 8

## What local port was the script listening on?

The listening port appeared in the **Arguments** field from the previous command.

### Answer

```
1348
```

---

# Question 9

## When did Jenny last log on?

```powershell
net user Jenny | findstr "Last"
```

### Answer

```
Never
```

---

# Question 10

## On what date did the compromise occur?

I opened File Explorer and browsed to:

```
C:\
```

Several recently created folders shared the same date, revealing when the compromise occurred.

### Answer

```
03/02/2019
```

---

# Question 11

## When were special privileges first assigned to a new logon?

I opened **Event Viewer** and navigated to:

```
Windows Logs
└── Security
```

Since there were hundreds of events, I created a **Custom View** using:

- Date: **03/02/2019**
- Time: **4:00 PM – 4:30 PM**
- Log: **Security**

I reviewed the earliest **Security Group Management** event.

### Answer

```
03/02/2019 4:04:47 PM
```

---

# Question 12

## What tool was used to dump Windows passwords?

A command prompt repeatedly referenced:

```
C:\TMP\mim.exe
```

I navigated to:

```
C:\TMP
```

Inside the directory I opened:

```
mim-out
```

The document referenced the password dumping utility.

### Answer

```
mimikatz
```

---

# Question 13

## What was the attacker's external Command & Control server IP?

I returned to the hosts file.

```
C:\Windows\System32\drivers\etc\hosts
```

Both **google.com** and **www.google.com** pointed to the same IP.

I compared the address against a legitimate DNS lookup from my host machine and confirmed the hosts file had been modified.

### Answer

```
76.32.97.132
```

---

# Question 14

## What extension did the uploaded web shell use?

I navigated to:

```
C:\inetpub\wwwroot
```

Inside the web root I found two Java Server Pages files.

### Answer

```
.jsp
```

---

# Question 15

## What was the last port opened by the attacker?

I opened:

```
Windows Defender Firewall with Advanced Security
```

Then selected:

```
Inbound Rules
```

I filtered by:

```
Rules without a Group
```

One suspicious rule appeared.

```
Allow outside connections for development
```

Opening the rule and checking the **Protocols and Ports** tab revealed the configured port.

### Answer

```
1337
```

---

# Question 16

## Which website was targeted for DNS poisoning?

Returning to the hosts file showed that Google's domain had been redirected to the attacker's server.

### Answer

```
google.com
```
