import docker
import os

# this is a copilot suggestion. crosscheck and make sure it works
client = docker.from_env()

# Function to copy file from host to container
def copy_to_container(container_name, source, target):
    # Create a tar file of the source file
    os.system(f"tar -cf /tmp/temp.tar -C / {source}")
    
    # Get the container
    container = client.containers.get(container_name)
    
    # Put the tar file into the container
    with open('/tmp/temp.tar', 'rb') as file:
        container.put_archive('/', file.read())
    
    # Move the file to the target location inside the container
    container.exec_run(f"mv /{source} {target}")
    
    # Cleanup
    os.remove("/tmp/temp.tar")

# Function to copy file from container to host
def copy_from_container(container_name, source, target):
    # Get the container
    container = client.containers.get(container_name)
    
    # Create a tar archive of the source file inside the container
    bits, stat = container.get_archive(source)
    
    # Write the tar file to a temporary file on the host
    with open('/tmp/temp.tar', 'wb') as file:
        for chunk in bits:
            file.write(chunk)
    
    # Extract the tar file to the target location on the host
    os.system(f"tar -xf /tmp/temp.tar -C {target}")
    
    # Cleanup
    os.remove("/tmp/temp.tar")

# Example usage
copy_to_container('your_container_name', 'path/to/host/file', '/container/target/path')
copy_from_container('your_container_name', '/container/source/file', 'path/to/host/target')