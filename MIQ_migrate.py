import requests
import json
import pandas as pd
import urllib3
from bs4 import BeautifulSoup
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class color:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    VIOLET = '\33[35m'
    BEIGE  = '\33[36m'
    WHITE  = '\33[37m'
    RED    = '\33[31m'
    YELLOW = '\33[33m'

    WARNING = '\033[93m'
    FAIL = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

# ManageIQ API endpoint
api_url = "https://manageiq.local/api"

# ManageIQ credentials
username = "SomeUsername
password = "Pass"

# Connect to ManageIQ API
session = requests.Session()
session.auth = (username, password)
session.verify = False

# Delete service using URL

def delete_service(url: str, session: requests.Session):
    """
    Delete a service or VM based on the provided URL using the specified requests Session.

    Args:
        url (str): The URL of the service or VM to be deleted.
        session (requests.Session): An existing requests Session object for making HTTP requests.

    Returns:
        Any: The response from the deletion request.
    """
    if len(url) == 0:
        print("Deleting Service or VM...   " + color.WARNING + "Service URL is not present!" + color.END)
        return
    
    try:
        delete_response = session.delete(url)
        delete_response.raise_for_status()  # Raise HTTPError for bad requests
        if 'vms' in url:
            print(f"VM successfully deleted: {url}")
        else:
            print(f"Service successfully deleted: {url}")
        return delete_response
    except requests.exceptions.RequestException as e:
        print(f"Error deleting {url}: {e}")
        return None

def update_description(url: str, desc: str, session: requests.Session) -> requests.Response:
    """
    Update the description using a POST request.

    Parameters:
    - url (str): The VM URL for the update.
    - desc (str): The new description to be set.
    - session (requests.Session): The pre-existing session object.

    Returns:
    - requests.Response: The HTTP response object.
    """
    update_data = {"action": "edit", "resource": {"description": f"{desc}"}}
    service_headers = {'Content-Type': 'application/json'}

    try:
        create_result = session.post(url, data=json.dumps(update_data), headers=service_headers)
        create_result.raise_for_status()  # Raise an HTTPError for bad responses
        print(f"Update successful")
        return create_result
    except requests.exceptions.RequestException as e:
        # Handle exceptions (e.g., connection errors, timeout)
        print(f"Error updating description: {e}")
        return None

def assign_tag(url: str, vmtype: str, category: str = 'vmtype', session: requests.Session):
    """
    Assign a tag to a VM or service.

    Parameters:
    - url (str): The URL for the assignment.
    - vmtype (str): The type of the VM or service.
    - category (str): The category for the assignment (default is 'vmtype').
    - session (requests.Session): The session object.

    Returns:
    - requests.Response: The HTTP response object.
    """
    # Constants
    LOCATION_CATEGORIES = {'b7': 'b7', 'sm22': 'sm22', 'metro': 'metro'}
    VM_TYPE_CATEGORIES = {'cloud': 'cloud', 'traditional': 'traditional'}

    # Normalize category
    category = str(category).lower()

    if 'location' in category:
        category = 'location'
        vmtype = LOCATION_CATEGORIES.get(str(vmtype).lower())

        if vmtype is None:
            print("VM Location is not found!!!")
            return 1

    elif 'vmtype' in category:
        category = 'vmtype'
        vmtype = VM_TYPE_CATEGORIES.get(str(vmtype).lower())

        if vmtype is None:
            print("VM type is not found!!!")
            return 1

    # URL and data preparation
    url_tags = f"{url}/tags"
    update_data = {"action": "assign", "resource": {"name": f"{vmtype}", "category": f"{category}"}}
    service_headers = {'Content-Type': 'application/json'}

    # HTTP request
    try:
        assign_tag_response = session.post(url_tags, data=json.dumps(update_data), headers=service_headers)
        assign_tag_response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error assigning tag: {e}")
        return None

    # Print information based on URL
    if "vms" in url:
        print(f"VM assigned tag: {color.BOLD}{color.BLUE}{vmtype.upper()}{color.END}!")
    elif "services" in url:
        print(f"Service assigned tag: {color.BOLD}{color.BLUE}{vmtype.upper()}{color.END}!")
    else:
        print(f"Assigned tag to the object with url - {url}: {color.BOLD}{color.BLUE}{vmtype.upper()}{color.END}!")

    return assign_tag_response

def get_vm_os(url: str, vm_name: str, session: requests.Session):
    """
    Get the operating system details for a VM.

    Parameters:
    - url (str): The URL for the VM resource.
    - vm_name (str): The name of the VM.
    - session (requests.Session): The session object.

    Returns:
    - dict: Dictionary containing OS details.
    """
    # Parameter validation
    if not url or not vm_name:
        print("URL or VM name is not provided!!!")
        return None

    vm_resource_url = url

    # Get tags for specified VM resource
    vm_os_url = f"{vm_resource_url}?expand=resources&attributes=operating_system"

    try:
        os_response = session.get(vm_os_url)
        os_response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error getting VM OS: {e}")
        return None

    os_data = os_response.json()
    
    os_name = os_data['operating_system']['product_name']
    
    if os_name:
        print(f"{vm_name} has OS {сolor.BOLD}{сolor.VIOLET}{os_name}{сolor.END}!")
    else:
        print(f"Operating system details not found for {vm_name}.")

    return {
        "data": os_data, 
        "os_details": os_data['operating_system'], 
        "os_name": os_data['operating_system']['product_name'], 
        "id": os_data['operating_system']['id']
    }

### Functions for update!!!
def get_vm_url(name: str, state: str):

    # Get virtual machine object with specified name and state ON and archived(unknown)
    vm_name= str(name)
    print("VM name: " + color.BOLD + color.CYAN + vm_name + color.END)
    vm_url = ''
    if state.lower() == 'archived':
        vm_url = f"{api_url}/vms?filter[]=name='{vm_name}'&filter[]=power_state='unknown'"

    elif state.lower() == 'on':
        vm_url = f"{api_url}/vms?filter[]=name='{vm_name}'&filter[]=power_state='on'"

        # Checking if there is VMs with state ON. If not checking with state Off
        vm_response = session.get(vm_url)
        vm_data = json.loads(vm_response.text)
        vm_len = len(vm_data["resources"])

        if  vm_len == 0:
            print("VM with state ON - Not found. Checking VM with state Off")
            vm_url = f"{api_url}/vms?filter[]=name='{vm_name}'&filter[]=power_state='off'"


    else:
        print("Unknown state for VM!")

    vm_response = session.get(vm_url)
    vm_data = json.loads(vm_response.text)

    vm_len = len(vm_data["resources"])
   
    if len(vm_data["resources"]) > 0:
        url = vm_data["resources"][0]['href']
        print(f" VM with state {state.upper()} resource url: ", url)

        return url, vm_data

    else:
         
        print(f"VM resource with name {vm_name} with state {state.upper()} doesn't exist!!!")
        return 1
        


def get_vm_tags(url: str, vm_name: str):

    # Get tags for VM object from its url

    if url is None:
        print(f"Url was not provided for VM with a name - {vm_name}!!!")
        return 1

    elif len(vm_name) == 0:
        print(f"VM name is not provided!!!")
        return 1

    elif url == 1:
        print(f"VM name is not provided!!!")
        return 1

    vm_resource_url = str(url)
    print("Extracting tags for VM resource url: ", vm_resource_url)

    # Get tags for specified VM resource
    vm_tags_url = f"{vm_resource_url}?expand=tags"
    

    tags_response = session.get(vm_tags_url)

    tags_data = json.loads(tags_response.text)

    # Initialize dict to keep vm tags info
    vm_tags = {}
    for i in tags_data['tags']:
        tag_list = []
        # Convert tags separated by / to the list
        tag_list = i['name'].replace("/managed/", '').split("/")
        # Add tag key and value to the dictionary
        vm_tags[tag_list[0]] = tag_list[1]

    
    for key, value in vm_tags.items():

        if key == 'vmtype':
            print(key  + " : " + color.GREEN + color.BOLD + value + color.END)
        elif key == 'business_group_id':
            print(key + " : " + color.BLUE + color.BOLD + value + color.END)
        elif key == 'environment':
            print(key + " : " + color.YELLOW + color.BOLD + value + color.END)
        elif key == 'network_location':
            print(key + " : " +color.CYAN + color.BOLD + value + color.END)
        elif key == "lifecycle":
            pass
        elif "folder_path" in str(key):
            pass
        else:
            print(key + " : " + value )
    
        
    print("Descripion: " + color.BOLD + f"{tags_data['description']}\n" + color.END)

    if 'vmtype' not in list(vm_tags.keys()):
    
        print("vmtype - " + color.BOLD + color.YELLOW + "Not found!" + color.END)        

    return {"tags":tags_data['tags'], "data": tags_data, "desc": tags_data['description'], "vmtype": vm_tags['vmtype']}

def get_service_url_tags(vm_resource_name: str):
    
    # Get service with name "VM - <vm_name>"
    vm_name = str(vm_resource_name)
    service_name = f"VM - {vm_name}"
    service_url = f"{api_url}/services?filter[]=name='{service_name}'"
    service_response = session.get(service_url)
    service_data = json.loads(service_response.text)
    
    # Extract url to Service resource from the data output
    if len(service_data["resources"]) == 0:
        # Trying to use capitalized vm name
        service_name = f"VM - {vm_name.upper()}"

        service_url = f"{api_url}/services?filter[]=name='{service_name}'"
        service_response = session.get(service_url)
        service_data = json.loads(service_response.text)

        if len(service_data["resources"]) > 0:
            subcount = int(service_data['subcount'])
            
            if subcount > 1:
                print(color.BOLD + color.RED + "There are " + str(subcount) + " service with the same name " + color.BLUE + service_name + color.END + "!")

                for i in range(0, subcount):
                    print(service_data["resources"][i]['href'])
                return 1

            else:
                service_resource_url = service_data["resources"][0]['href']
        
        else:
            print("Service with the name " + color.BOLD + color.BLUE + vm_name + color.WARNING + " Not Exists!" + color.END)
            return {'url': "", 'tags': "", 'data': "" }

    else:
        subcount = int(service_data['subcount']) 
        if subcount > 1:
            print(color.BOLD + color.RED + "There are " + str(subcount) + " service with the same name " + color.BLUE + service_name + color.END + "!")

            for i in range(0, subcount):
                print(service_data["resources"][i]['href'])
            return 1

        else:            
            service_resource_url = service_data["resources"][0]['href']
     
    print(f" Service resource url for {vm_resource_name}: ", service_resource_url)

    # Get tags for specified VM Service resource
    service_tags_url = f"{service_resource_url}?expand=tags"
    service_tags_response = session.get(service_tags_url)
    service_tags_data = json.loads(service_tags_response.text)

    user_id = service_tags_data['evm_owner_id']
    user_info = get_user(user_id)
    print(color.BOLD + color.CYAN + user_info[0] + color.END)
    print(user_info[1])

    return {'url': service_resource_url, 'tags': service_tags_data['tags'], 'data': service_tags_data, 'user': user_info}

def get_user(user_id: str):
    
    # Get user information by id
    user_id = str(user_id)
    user_url = f"{api_url}/users/{user_id}"
    user_response = session.get(user_url)
    user_data = json.loads(user_response.text)

    user_name = [user_data.get(key) for key in ['name', 'email']]
    
    return user_name
