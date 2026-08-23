well this room was completed faster than I expected. Room - Neighbor

## Difficulty - Easy

---

Machine IP: 10.114.139.176

---

There was a webpage on this address http://10.114.139.176
I entered it and I was prompted to a login page

First thing I did was to open the page source and there was a comment:

<!-- use guest:guest credentials until registration is fixed. "admin" user account is off limits!!!!! -->

I tried as username and passwd: guest

and I logged in as guest obviosuly

I saw that the address changed to:
http://10.114.139.176/profile.php?user=guest

From all these comments in the src I was tempted to try IDOR since this website seems to be in super
early stage of development and probably nothing is working as its supposed to

so I change the user=guest to user=admin

and I was prompted to the admin page where the flag is

So there it is
<details>
<summary>Spoiler Alert!</summary>

flag{66be95c478473d91a5358f2440c7af1f}

</details>
