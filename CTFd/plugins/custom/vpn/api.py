import json
import urllib3
import requests
from flask import abort

class VPNConnector:
    """
    A class to manage Cyberex VPN operations.
    Author: PFC Ferdinand P Lazarte (Inf) PA
    DATE: March 2024
    """

    def __init__(self):
        """
        Initializes the VPNConnector with necessary configuration.
        """
        self.headers = {
            "content-type": "application/json",
            "X-VPNADMIN-HUBNAME": "Administrator",
            "X-VPNADMIN-PASSWORD": "Cyber@1992",
        }
        self.gateway = "https://157.20.8.39:5555/api"
        self.hub_name = "Cyberex-VPN"
        self.group_name = "Cyberex-Participants"

    def _send_request(self, method, params):
        """
        Sends a request to the VPN server.

        Args:
            method (str): The RPC method to call.
            params (dict): The parameters for the RPC method.

        Returns:
            dict: The server's response as a dictionary.

        Raises:
            Exception: If the request fails or returns a non-200 status code.
        """
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        payload = {
            "jsonrpc": "2.0",
            "id": "rpc_call_id",
            "method": method,
            "params": params,
        }
        response = requests.post(
            url=self.gateway, headers=self.headers, data=json.dumps(payload), verify=False
        )
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(
                f"{method} failed with status code {response.status_code}: {response.text}"
            )

    def get_server_info(self):
        """
        Retrieves information about the VPN server.

        Returns:
            dict: Server information.
        """
        return self._send_request("Test", {"IntValue_u32": 0})

    def get_server_status(self):
        """
        Retrieves the VPN server's current status.

        Returns:
            dict: Server status.
        """
        return self._send_request("GetServerStatus", {})

    def create_user(self, username, user_full_name, user_password):
        """
        Creates a new VPN user.

        Args:
            username (str): The username for the new user.
            user_full_name (str): The full name of the user.
            user_password (str): The password for the user.

        Returns:
            dict: The server's response to the user creation request.
        """
        params = {
            "HubName_str": self.hub_name,
            "Name_str": username,
            "Realname_utf": user_full_name,
            "GroupName_str": self.group_name,
            "AuthType_u32": 1,
            "Auth_Password_str": user_password,
            "UsePolicy_bool": False,
        }
        return self._send_request("CreateUser", params)

    def delete_user(self, username):
        """
        Deletes a VPN user.

        Args:
            username (str): The username of the user to delete.

        Returns:
            dict: The server's response to the deletion request.
        """
        params = {
            "HubName_str": self.hub_name,
            "Name_str": username,
        }
        return self._send_request("DeleteUser", params)
