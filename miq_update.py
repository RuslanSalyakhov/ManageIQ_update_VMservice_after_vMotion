import requests
import json

# ManageIQ API endpoint
api_url = "https://<manageiq_host>/api"

# ManageIQ credentials
username = "<username>"
password = "<password>"

# Virtual machine name
vm_name = "<vm_name>"

# Connect to ManageIQ API
session = requests.Session()
session.auth = (username, password)
session.verify = False

# Get virtual machine object with specified name and state ON
vm_url = f"{api_url}/vms?filter[]=name='{vm_name}'&filter[]=power_state='on'"
vm_response = session.get(vm_url)
vm_data = json.loads(vm_response.text)

# Print tags assigned to virtual machine object
vm_tags = vm_data["resources"][0]["tags"]
print(f"Tags assigned to {vm_name}: {vm_tags}")

# Get service with name "VM - <vm_name>"
service_name = f"VM - {vm_name}"
service_url = f"{api_url}/services?filter[]=name='{service_name}'"
service_response = session.get(service_url)
service_data = json.loads(service_response.text)

# Get tags assigned to service
service_tags = service_data["resources"][0]["tags"]
print(f"Tags assigned to {service_name}: {service_tags}")

# Remove service from inventory
confirm = input("Do you want to remove the service? (Y/N): ")
if confirm.lower() == "y":
    service_id = service_data["resources"][0]["id"]
    delete_url = f"{api_url}/services/{service_id}"
    session.delete(delete_url)

# Get archived virtual machine object with specified name
archived_vm_url = f"{api_url}/vms?filter[]=name='{vm_name}'&filter[]=power_state='archived'"
archived_vm_response = session.get(archived_vm_url)
archived_vm_data = json.loads(archived_vm_response.text)

# Assign tags from archived virtual machine object to ON virtual machine object
confirm = input("Do you want to assign tags from archived VM to ON VM? (Y/N): ")
if confirm.lower() == "y":
    archived_vm_tags = archived_vm_data["resources"][0]["tags"]
    vm_id = vm_data["resources"][0]["id"]
    update_url = f"{api_url}/vms/{vm_id}"
    update_data = {"action": "edit", "resource": {"tags": archived_vm_tags}}
    session.post(update_url, json=update_data)

# Remove archived virtual machine object
confirm = input("Do you want to remove the archived VM? (Y/N): ")
if confirm.lower() == "y":
    archived_vm_id = archived_vm_data["resources"][0]["id"]
    delete_url = f"{api_url}/vms/{archived_vm_id}"
    session.delete(delete_url)
