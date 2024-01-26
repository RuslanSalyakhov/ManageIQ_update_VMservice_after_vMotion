import requests
import json
import pandas as pd
import urllib3
from bs4 import BeautifulSoup
from typing import Union
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

def delete_service(url: str, session: requests.Session = session):
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

def update_description(url: str, desc: str, session: requests.Session = session) -> requests.Response:
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

def assign_tag(url: str, vmtype: str, category: str = 'vmtype', session: requests.Session = session):
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

def get_vm_os(url: str, vm_name: str, session: requests.Session = session):
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

def get_vm_url(name: str, state: str = 'on', api_url: str = api_url, session: requests.Session = session):
    """
    Get the URL for a virtual machine based on its name and state.

    Parameters:
    - name (str): The name of the virtual machine.
    - state (str): The state of the virtual machine ('on', 'off', 'archived').
    - session (requests.Session): The session object.

    Returns:
    - str: The URL of the virtual machine.
    """
    # Parameter validation
    if not name:
        print("VM name is not provided!!!")
        return None
    
    # Constants
    STATES = {'on': 'on', 'off': 'off', 'archived': 'archived'}

    # Normalize state
    state = STATES.get(state.lower())
    if state is None:
        print("Unknown state for VM!")
        return None
        
    # Get virtual machine object with specified name and state ON and archived(unknown)
    vm_name= str(name)
    vm_url = ''

    # Define a list containing originally entered name and lower and upper case form
    name_forms = [vm_name, vm_name.lower(), vm_name.upper()]
    forms = ['lowercase', 'uppercase', 'placeholder']
    
    if state == 'archived':
        
        for name, form in zip(name_forms, forms):
            vm_url = f"{api_url}/vms?filter[]=name='{name}'&filter[]=power_state='unknown'"

            # Checking uf the VM resource exists
            vm_response = session.get(vm_url)
            vm_data = json.loads(vm_response.text)
            vm_len = len(vm_data["resources"])
        
            if vm_len > 0:
                vm_name = name
                break  # Exit the loop if a matching resource is found

            if forms.index(form) < len(forms) - 1:
                print(f"VM with state archived - Not found. Checking for VM name {color.YELLOW}{name}{color.END} in {form} form")

        if vm_len == 0:
            print(f"VM resource with name {name} and state {state.upper()} doesn't exist!!!")
            return None

    elif state == 'on':
        
        vm_url = f"{api_url}/vms?filter[]=name='{vm_name}'&filter[]=power_state='on'"

        # Checking if there is VMs with state ON. If not checking with state Off
        vm_response = session.get(vm_url)
        vm_data = json.loads(vm_response.text)
        vm_len = len(vm_data["resources"])

        if  vm_len == 0:
            print("VM with state ON - Not found. Checking for VM name in lowercase form")

            vm_url = f"{api_url}/vms?filter[]=name='{vm_name.lower()}'&filter[]=power_state='on'"

            vm_response = session.get(vm_url)
            vm_data = json.loads(vm_response.text)
            vm_len = len(vm_data["resources"])

            if vm_len == 0:

                print("VM with state ON - Not found. Checking VM with state Off")
                vm_url = f"{api_url}/vms?filter[]=name='{vm_name}'&filter[]=power_state='off'"

                vm_response = session.get(vm_url)
                vm_data = json.loads(vm_response.text)
                vm_len = len(vm_data["resources"])

                if vm_len == 0:
                    print("VM with state OFF - Not found. Checking for VM name in lowercase form")
                    vm_url = f"{api_url}/vms?filter[]=name='{vm_name.lower()}'&filter[]=power_state='off'"

                    vm_response = session.get(vm_url)
                    vm_data = json.loads(vm_response.text)
                    vm_len = len(vm_data["resources"])

                    if vm_len == 0:
                         print("VM with state OFF - Not found. Checking for VM name in ANY case form")
                         vms_url =  f"{api_url}/vms?expand=resources&attributes=name,power_state"

                         vms_response = session.get(vms_url)
                         vms_data = json.loads(vms_response.text)

                         max_len =  float('inf')
                         found_flag = False
                         for i in vms_data['resources']:
                             
                             if str(vm_name).lower() in str(i['name']).lower():
                            
                                 vm_url = i['href']
                                 resource_name = i['name']
                                 vm_state = i['power_state']
                                 print(f"VM with state {str(vm_state).upper()} with url " + color.BOLD + str(vm_url) + "  has name - " + color.BOLD + color.BLUE + str(resource_name) + color.END + " with SOME lower case letters used " + color.RED + "INCORRECTLY!" + color.END)
                                
                                 if len(vm_name) == len(resource_name):
                                    
                                    return vm_url, vms_data

                                 elif (len(vm_name) < len(resource_name)) and (len(resource_name) < max_len):
                                     max_len = len(resource_name)
                                     result_url = vm_url
                                     result_name = resource_name 
                                     result_state = vm_state
                                     found_flag = True

                         if found_flag:

                             print(f"Finally for VM " + color.BOLD + color.CYAN + str(vm_name) + color.END + f" with state {str(result_state).upper()} with url " + color.BOLD + str(result_url) + "  has name - " + color.BOLD + color.BLUE + str(result_name) + color.END)
                             return result_url, vms_data 
                             
                         else:
                            print(f"VM resource with name {vm_name} with state {state.upper()} doesn't exist!!!")
                            return 1   
   
    if len(vm_data["resources"]) > 0:
        url = vm_data["resources"][0]['href']
        print(f"VM with state {state.upper()} with url " + color.BOLD + str(url) + "  has name - " + color.BOLD + color.BLUE + str(vm_name) + color.END)
        #print(f" VM with state {state.upper()} resource url: ", url)
        return url, vm_data

    else:
        print(f"VM resource with name {vm_name} with state {state.upper()} doesn't exist!!!")
        return 1
        
def get_vm_tags(url: str, session: requests.Session = session) -> Dict[str, Union[Dict[str, str], Dict[str, str], str, str]]:
    """
    Get tags for a VM object from its URL.

    Parameters:
    - url (str): URL of the VM resource.
    - vm_name (str): Name of the VM.
    - session: Requests session object.

    Returns:
    - Dict[str, Union[Dict[str, str], Dict[str, str], str, str]]: Dictionary containing tags, data, description, and vmtype.
    """

    # Get tags for VM object from its url

    if url is None or url == 1:
        raise ValueError(f"Invalid url input for VM!!!")

    vm_resource_url = str(url)
    print("Extracting tags for VM resource url: ", vm_resource_url)

    # Get tags for specified VM resource
    vm_tags_url = f"{vm_resource_url}?expand=resources&attributes=tags"    
    tags_response = session.get(vm_tags_url)

    tags_data = json.loads(tags_response.text)
    vm_name = tags_data['name']
    print(f"VM name: {color.BOLD}{color.BEIGE}{vm_name}{color.END}")

    # Initialize dict to keep vm tags info
    vm_tags = {}
    for i in tags_data['tags']:
        tag_list = []
        # Convert tags separated by / to the list
        tag_list = i['name'].replace("/managed/", '').split("/")
        # Add tag key and value to the dictionary
        vm_tags[tag_list[0]] = tag_list[1]

    #print(vm_tags)
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
    
        
    print("Description: " + color.BOLD + f"{tags_data['description']}\n" + color.END)
    
    if 'vmtype' not in list(vm_tags.keys()):
        print("vmtype - " + color.BOLD + color.YELLOW + "Not found!" + color.END)
        vm_tags['vmtype'] = ''  
        
    #print(f"Tags assigned to {vm_name}: {tags_data['tags']}")
    #pd_tags = pd.DataFrame.from_dict(tags_data['tags'])
    #pd_tags.index.names = [f'{vm_name}']
    #display(pd_tags[['id', 'name']])

    return {"tags":vm_tags, "data": tags_data, "desc": tags_data['description'], "vmtype": vm_tags['vmtype']}

# ПРИМЕР КОДА С КОММЕНТАРИЯМИ ОТ GPT
def get_vm_tags(session, url: str, vm_name: str) -> Dict[str, Union[Dict[str, str], Dict[str, str], str, str]]:
    """
    Get tags for a VM object from its URL.

    Parameters:
    - session: Requests session object.
    - url (str): URL of the VM resource.
    - vm_name (str): Name of the VM.

    Returns:
    - Dict[str, Union[Dict[str, str], Dict[str, str], str, str]]: Dictionary containing tags, data, description, and vmtype.
    """

    if url is None or len(vm_name) == 0 or url == 1:
        raise ValueError(f"Invalid input for VM with name - {vm_name}!!!")

    vm_resource_url = str(url)
    print("Extracting tags for VM resource url: ", vm_resource_url)

    vm_tags_url = f"{vm_resource_url}?expand=tags"
    tags_response = session.get(vm_tags_url)
    tags_data = json.loads(tags_response.text)

    vm_tags = {}

    for i in tags_data['tags']:
        tag_list = i['name'].replace("/managed/", '').split("/")
        vm_tags[tag_list[0]] = tag_list[1]

    for key, value in vm_tags.items():
        print(format_key_value(key, value))

    print(f"Description: {tags_data['description']}\n")

    if 'vmtype' not in vm_tags:
        print("vmtype - Not found!")
        vm_tags['vmtype'] = ''

    return {"tags": vm_tags, "data": tags_data, "desc": tags_data['description'], "vmtype": vm_tags.get('vmtype', '')}

    
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

        while len(service_data) <= 1:
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
            service_url = f"{api_url}/services?expand=resources&attributes=name&filter[]=name='*{vm_name}'"
            service_response = session.get(service_url)
            service_data = json.loads(service_response.text)

            while len(service_data) <= 1:
                service_response = session.get(service_url)
                service_data = json.loads(service_response.text)
                
            if len(service_data["resources"]) == 0:

                service_url = f"{api_url}/services?expand=resources&attributes=name"
                service_response = session.get(service_url)
                service_data = json.loads(service_response.text)
                found = False
                while len(service_data) <= 1:
                    service_response = session.get(service_url)
                    service_data = json.loads(service_response.text)

                max_len =  float('inf')
                found_flag = False
                result_url = ''
                result_name = ''
                
                for i in service_data['resources']:
                     if str(i['name']).startswith('VM') and str(vm_name).lower() in str(i['name']).lower():

                         service_resource_url = i['href']
                         vm_resource_name = i['name']
                         
                         if len(service_name) == len(vm_resource_name):
                            print("Service name with url " + color.BOLD + str(service_resource_url) + "  has name - " + color.BOLD + color.BLUE + str(vm_resource_name) + color.END + " with SOME lower case letters used " + color.RED + "INCORRECTLY!" + color.END)
                            break

                         elif (len(service_name) < len(vm_resource_name)) and (len(vm_resource_name) < max_len):
                            max_len = len(vm_resource_name)
                            result_url = service_resource_url
                            result_name = vm_resource_name 
                            found_flag = True

                if found_flag:

                     service_resource_url = result_url 
                     vm_resource_name = result_name

                     print("Service name with url " + color.BOLD + str(service_resource_url) + "  has name - " + color.BOLD + color.BLUE + str(vm_resource_name) + color.END + " with SOME lower case letters used " + color.RED + "INCORRECTLY!" + color.END)

                elif not found_flag and (len(service_name) != len(vm_resource_name)):
                     print("Service with the name " + color.BOLD + color.BLUE + vm_name + color.WARNING + " Not Exists!\n" + color.END)
                     return {'url': "", 'tags': "", 'data': "" }

            else:
                service_resource_url = service_data["resources"][0]['href']
                #print(service_data)
                vm_resource_name = service_data["resources"][0]['name']
                print("Service name " + color.BOLD + color.BLUE + str(vm_resource_name) + color.END + " extra whitespaces typed " + color.YELLOW + "INCORRECTLY!" + color.END)

    else:
        subcount = int(service_data['subcount']) 
        if subcount > 1:
            print(color.BOLD + color.RED + "There are " + str(subcount) + " service with the same name " + color.BLUE + service_name + color.END + "!")

            for i in range(0, subcount):
                print(service_data["resources"][i]['href'])
            return 1

        else:            
            service_resource_url = service_data["resources"][0]['href']

    # FORMATTED OUTPUT  
    #print("For VM name " + color.BOLD + color.BLUE + str(vm_name) + color.END + " Service resource name " + color.BOLD + color.CYAN + str(vm_resource_name) + color.END + " has url: ", service_resource_url)
    print("For VM name " + str(vm_name) + f' - Service resource name "{service_name}"' + " has url: ", service_resource_url)
    
    # Get tags for specified VM Service resource
    service_tags_url = f"{service_resource_url}?expand=tags"
    service_tags_response = session.get(service_tags_url)
    service_tags_data = json.loads(service_tags_response.text)
    
    #print(f"Tags assigned to {vm_name}: {service_tags_data['tags']}")
    # Print list of tags assigned to the service
    #for i in service_tags_data['tags']:
    #    print(i['name'].replace('/managed/', ''))

    user_id = service_tags_data['evm_owner_id']
    if len(user_id) > 0:
        user_info = get_user(user_id)
    else: 
        print(color.BOLD + color.RED + "user_id contains empty value!!!\n" + color.END)

    if user_info != None:
        pass
        #Print user name and email 
        print(color.BOLD + color.CYAN + str(user_info[0]) + color.END)
        print(user_info[1], "\n")
    else:
        print(color.BOLD + f"user_info for user_id {user_id} is " + color.RED + "NONE" + color.BLUE + "value!!!\n" + color.END)
        return None
    #print(str('\n'.join(user_info)))
    #print("\n")
    #print(f"User info: {', '.join(user_info)}\n")
    #print(f"User info: {user_info}\n")

    return {'url': service_resource_url, 'tags': service_tags_data['tags'], 'data': service_tags_data, 'user': user_info}


def get_user(user_id: str):
    
    # Get user information by id
    user_id = str(user_id)
    user_url = f"{api_url}/users/{user_id}"
    user_response = session.get(user_url)
    user_data = json.loads(user_response.text)

    user_name = [user_data.get(key) for key in ['name', 'email']]
    
    return user_name

# QUOTA GET and UPDATE functions
def update_quota(uri_dict, cpu=0, memory=0, storage=0):
    result = []
    flag = False
    value_ = ''
    for i in uri_dict:
        if i == 'storage' and storage != 0:
            value_gb = uri_dict[i]['storage_gb'] + float(storage)
            print("Storage new value :", value_gb, "GB")
            value_ = value_gb * (1024*1024*1024)
            url = uri_dict[i]['storage_uri']
            flag = True

        elif i == 'memory' and memory != 0:
            value_gb = uri_dict[i]['memory_gb'] + float(memory)
            print("Memory new value :", value_gb, "GB")
            value_ = value_gb * (1024*1024*1024)
            url = uri_dict[i]['memory_uri']
            flag = True
        elif i == 'cpu' and cpu != 0:
            value_ = int(uri_dict[i]['cpu_count']) + int(cpu)
            print("CPU new value :", value_, "cores")

            url = uri_dict[i]['cpu_uri']
            flag = True

        update_data = { "action": "edit",  
                        "resource" : {
                                    "value":f"{value_}"
                                    }}
    
        if flag:
            update_quota = session.post(str(url), data=json.dumps(update_data), headers=service_headers)
            flag = False
            result.append(update_quota)

    return result

def get_tenant_uri(ci_name: str, api_url: str = api_url, session=session):
    # ci_name in format 'rsb_ci85262'
    tenant_url = f"{api_url}/tenants?expand=resources&attributes=name&filter[]=name={str(ci_name)}"
    #tenant_url = f"https://manageiqr00.gts.rus.socgen/api/tenants?expand=resources&attributes=name&filter[]=name={str(ci_name)}"

    tenant_response = session.get(tenant_url)
    tenant_data = json.loads(tenant_response.text)
    uri = tenant_data['resources'][0]['href']
    print(f"Tenant uri: {color.CYAN}{uri}{color.END}")

    return uri

def get_tenant_quota(tenant_uri: str, session=session):
    # ci_name in format 'rsb_ci85262'
    quota_url = f"{str(tenant_uri)}/quotas?expand=resources&attributes=name,value,unit,used,available,total"

    quota_response = session.get(quota_url)
    quota_data = json.loads(quota_response.text)

    for q in quota_data['resources']:
        if q['name'] == 'storage_allocated':
            storage = float(q['value'])/(1024*1024*1024)
            storage_uri = q['href']
            storage_used = round(float(q['used'])/(1024*1024*1024), 3)
            storage_avail = round(float(q['available'])/(1024*1024*1024), 3)
            print(f"Storage total quota:\t {color.BLUE}{storage}{color.END} GB;\tUsed: {color.YELLOW}{storage_used}{color.END} GB;\tAvailable: {color.GREEN}{storage_avail}{color.END} GB")

        elif q['name'] == 'mem_allocated':
            memory = float(q['value'])/(1024*1024*1024)
            memory_uri = q['href']
            memory_used = float(q['used'])/(1024*1024*1024)
            memory_avail = float(q['available'])/(1024*1024*1024)
            print(f"Memory total quota:\t {color.BLUE}{memory}{color.END} GB;\tUsed: {color.YELLOW}{memory_used}{color.END} GB;\t\tAvailable: {color.GREEN}{memory_avail}{color.END} GB")


        elif q['name'] == 'cpu_allocated':
            cpu = int(q['value'])
            cpu_uri = q['href']
            cpu_used = q['used']
            cpu_avail = q['available']
            print(f"CPU total quota:\t {color.BLUE}{cpu}{color.END};\t\tUsed: {color.YELLOW}{cpu_used}{color.END};\t\tAvailable: {color.GREEN}{cpu_avail}{color.END}")

    return {'storage': {'name': 'storage_allocated', 'storage_gb': storage, 'storage_uri': storage_uri}, 'memory': {'name': 'mem_allocated', 'memory_gb': memory, 'memory_uri': memory_uri}, 'cpu':  {'name': 'cpu_allocated', 'cpu_count': cpu, 'cpu_uri': cpu_uri}}

def get_vm_os(url: str, session = session):

    if url is None:
        print("Url was not provided for VM !!!")
        return 1

    elif url == 1:
        print("Url was not provided for VM !!!")
        return 1

    vm_resource_url = str(url)
    #print("Extracting OS for VM resource url: ", vm_resource_url)

    # Get tags for specified VM resource
    vm_os_url = f"{vm_resource_url}?expand=resources&attributes=operating_system"

    os_response = session.get(vm_os_url)

    os_data = json.loads(os_response.text)
    vm_name = os_data['name']
    print(vm_name, "has OS " + color.BOLD + color.VIOLET + os_data['operating_system']['product_name'] +  color.END  + "!")

    return {"data": os_data, "os_details": os_data['operating_system'], "os_name": os_data['operating_system']['product_name'], "id": os_data['operating_system']['id']}

# Checking if service attached to VM and updating attached service name

def get_vm_service(url: str,  session = session):
    """
    Get a service attached to the VM based on the provided URL using the specified requests Session.

    Args:
        url (str): The URL of the VM.
        session (requests.Session): An existing requests Session object for making HTTP requests.

    Returns:
    - dict: Dictionary containing details of service attached to the specified VM
    """

    vm_name = ''

    if url is None:
        print(f"Url was not provided for VM with a name - {vm_name}!!!")
        return 1

    elif url == 1:
        print(f"URL is not provided!!!")
        return 1
    
    elif len(url) == 0:
        print(f"URL is not provided!!!")
        return 1

    vm_resource_url = str(url)
    #print("Extracting OS for VM resource url: ", vm_resource_url)

    # Get tags for specified VM resource
    vm_svc_url = f"{vm_resource_url}?expand=resources&attributes=service"

    svc_response = session.get(vm_svc_url)

    svc_data = json.loads(svc_response.text)

    vm_name = str(svc_data['name'])
    if svc_data['service'] == None:
        print(vm_name, "has " + color.BOLD + color.RED + "NO SERVICE ATTACHED" +  color.END  + "!")
        return 1

    else:
        print(color.BOLD + color.GREEN + vm_name + color.END, "has service attached with the name:  " + color.BOLD + color.VIOLET + svc_data['service']['name'] +  color.END  + "!")

    return {"data": svc_data, "svc_details": svc_data['service'], "svc_name": svc_data['service']['name'], "id": svc_data['service']['id'], 'vm_name': vm_name}

def update_service_name(service_id: Union[int, str], vm_name: str, api_url: str = 'https://manageiqr00.gts.rus.socgen/api'):

    service_headers = { 'Content-Type': 'application/json'}

    service_url = f"{api_url}/services/{str(service_id)}"

    new_name = f"VM - {str(vm_name).upper()}"
    update_data = { "action": "edit",  
                    "resource" : {"name" : new_name}}
    service_headers = { 'Content-Type': 'application/json'}
    
    try:
        print("Renaming service to " + color.BOLD + color.BLUE + str(new_name) + color.END)
        resp = session.post(str(service_url), data=json.dumps(update_data), headers=service_headers)
        resp.raise_for_status()
        return resp
    
    except requests.HTTPError as ex:
        # possibly check response for a message
        status_code = ex.response.status_code
        print("Status code: ", status_code)
        raise ex  
        
    except requests.Timeout:
        print("Request got timeout on server!")
        return None

