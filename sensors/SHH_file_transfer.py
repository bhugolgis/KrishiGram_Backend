import subprocess

def send_file_via_ssh(local_file_path, remote_file_path, password):
    # ssh_command = f"sshpass -p '{password}' scp -P 4022 {remote_file_path} {local_file_path}"
    copy_ssh_command = f"scp -P 4022 -i ~/.ssh/id_rsa climate@login.iitb.ac.in:{remote_file_path} {local_file_path} "

    try:
        subprocess.run(copy_ssh_command, shell=True, check=True)
        print(f"File '{remote_file_path}' sent to '{local_file_path}' successfully.")
      
        delete_ssh_command = f"ssh -p 4022 -i ~/.ssh/id_rsa climate@login.iitb.ac.in rm -f {remote_file_path} "


        subprocess.run(delete_ssh_command, shell=True, check=True)
        print(f"File '{remote_file_path}' deleted from remote folder.")
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")

# Example usage
local_file_path = "D:/krishiGram_backend/Krsuhi/"
remote_file_path = "/admin/climate/soilsensor/data.xlsx"
password = "soil$climate2023"

send_file_via_ssh(local_file_path, remote_file_path, password)



# ssh-keygen
# cat ~/.ssh/id_rsa.pub | ssh -p 4022 climate@login.iitb.ac.in "mkdir -p ~/.ssh && cat >> ~/.ssh/authorized_keys"