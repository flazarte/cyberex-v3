
import json
import os
import requests, urllib3
from flask import abort
from pprint import pp, pprint #for Debugging purpose only remove in Production

#Integration of Cyberex SecT-eX VPN Automation
#VPN Username Super User
CYBEREX_VPN_USERNAME = "Administrator"
CYBEREX_VPN_PASSWORD = "Cyber@1992"
CYBEREX_VPN_URL = "https://121.58.248.18/api/"
CYBEREX_VPN_HUBNAME = "Cyberex-VPN"
CYBEREX_VPN_GROUP_NAME = "Cyberex-Participants"

class VPNConnector:
    """
    A class to connect to a Cyberex VPN server and retrieve server information.
    Author: PFC Ferdinand P Lazarte (Inf) PA
    DATE: March 2024
    """
    
    def __init__(self):
        """
        Initializes the VPNConnector class.

        Args:
            username (str): The username for authentication.
            password (str): The password for authentication.
            gateway (str): The URL of the VPN server.
        """

  
        self.headers = {'content-type': 'application/json',
                            'X-VPNADMIN-HUBNAME': CYBEREX_VPN_USERNAME,
                            'X-VPNADMIN-PASSWORD': CYBEREX_VPN_PASSWORD,
                        }
        self.gateway = CYBEREX_VPN_URL
        self.hubname = CYBEREX_VPN_HUBNAME
        self.groupname = CYBEREX_VPN_GROUP_NAME
    
    #get Cyberex VPN Server Info
    def GetServerInfo(self):

        payload = {
            "jsonrpc": "2.0",
            "id": "rpc_call_id",
            "method": "Test",
            "params": {
                "IntValue_u32": 0
            }
        }
        
        # disable warnings
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        #submit response to vpn server
        response = requests.request("POST", url=self.gateway, headers=self.headers, data = json.dumps(payload),  verify=False)
        #pprint({"status_code":response.status_code})
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Request failed with status code: {response.status_code}")
        

    #get Get Server Status
    def GetServerStatus(self):

        payload = {
                    "jsonrpc": "2.0",
                    "id": "rpc_call_id",
                    "method": "GetServerStatus",
                    "params": {}
                }
        
        # disable warnings
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        #submit response to vpn server
        response = requests.request("POST", url=self.gateway, headers=self.headers, data = json.dumps(payload),  verify=False)
        #pprint({"status_code":response.status_code})
        if response.status_code == 200:
            return response.json()
        else:
            return abort(500, "Cyberex VPN Connection Error!")
            #raise Exception(f"Request failed with status code: {response.status_code}")
        
    #get Create Cyberex VPN User based on their created user credentials
    def CreateUser(self, username, user_full_name, user_password):
        false = False
        payload = {
                    "jsonrpc": "2.0",
                    "id": "rpc_call_id",
                    "method": "CreateUser",
                    "params": {
                        "HubName_str": self.hubname,
                        "Name_str": username,
                        "Realname_utf": user_full_name,
                        "GroupName_str": self.groupname,
                        "Note_utf": "",
                        "ExpireTime_dt": "",
                        "AuthType_u32": 1,
                        "Auth_Password_str": user_password,
                        "UserX_bin": "",
                        "Serial_bin": "",
                        "CommonName_utf": "auth_rootcert_commonname",
                        "RadiusUsername_utf": "auth_radius_radiususername",
                        "NtUsername_utf": "auth_nt_ntusername",
                        "UsePolicy_bool": false,
                        "policy:Access_bool": false,
                        "policy:DHCPFilter_bool": false,
                        "policy:DHCPNoServer_bool": false,
                        "policy:DHCPForce_bool": false,
                        "policy:NoBridge_bool": false,
                        "policy:NoRouting_bool": false,
                        "policy:CheckMac_bool": false,
                        "policy:CheckIP_bool": false,
                        "policy:ArpDhcpOnly_bool": false,
                        "policy:PrivacyFilter_bool": false,
                        "policy:NoServer_bool": false,
                        "policy:NoBroadcastLimiter_bool": false,
                        "policy:MonitorPort_bool": false,
                        "policy:MaxConnection_u32": 0,
                        "policy:TimeOut_u32": 0,
                        "policy:MaxMac_u32": 0,
                        "policy:MaxIP_u32": 0,
                        "policy:MaxUpload_u32": 0,
                        "policy:MaxDownload_u32": 0,
                        "policy:FixPassword_bool": false,
                        "policy:MultiLogins_u32": 0,
                        "policy:NoQoS_bool": false,
                        "policy:RSandRAFilter_bool": false,
                        "policy:RAFilter_bool": false,
                        "policy:DHCPv6Filter_bool": false,
                        "policy:DHCPv6NoServer_bool": false,
                        "policy:NoRoutingV6_bool": false,
                        "policy:CheckIPv6_bool": false,
                        "policy:NoServerV6_bool": false,
                        "policy:MaxIPv6_u32": 0,
                        "policy:NoSavePassword_bool": false,
                        "policy:AutoDisconnect_u32": 0,
                        "policy:FilterIPv4_bool": false,
                        "policy:FilterIPv6_bool": false,
                        "policy:FilterNonIP_bool": false,
                        "policy:NoIPv6DefaultRouterInRA_bool": false,
                        "policy:NoIPv6DefaultRouterInRAWhenIPv6_bool": false,
                        "policy:VLanId_u32": 0,
                        "policy:Ver3_bool": false
                    }
                }
        
        # disable warnings
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        #submit response to vpn server
        response = requests.request("POST", url=self.gateway, headers=self.headers, data = json.dumps(payload),  verify=False)
        #pprint({"status_code":response.status_code})
        if response.status_code == 200:
            return response.json()
        else:
            return abort(500, "Cyberex VPN Connection Error!")
            #raise Exception(f"Request failed with status code: {response.status_code}")
        
    #get Delete User
    def DeleteUser(self, username):

        payload = {
                    "jsonrpc": "2.0",
                    "id": "rpc_call_id",
                    "method": "DeleteUser",
                    "params": {
                        "HubName_str": self.hubname,
                        "Name_str": username
                    }
                }

        
        # disable warnings
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        #submit response to vpn server
        response = requests.request("POST", url=self.gateway, headers=self.headers, data = json.dumps(payload),  verify=False)
        #pprint({"status_code":response.status_code})
        if response.status_code == 200:
            return response.json()
        else:
            return abort(500, "Cyberex VPN Connection Error!")
            #raise Exception(f"Request failed with status code: {response.status_code}")
        