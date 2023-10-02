# cs356-networking
This program is used to discover the topology, including the switches and hosts in the network using RYU controller. It computes shortest path between two hosts based on the cost function provided. It also takes user input to request connection based on src and dest hosts, service request(IPv4 and MAC) and Bandwidth required.

 ## Running the project

1) Create a virtual environment in python3.9
2) Activate the virtual environment
3) Install the required dependencies using "pip install -r requirements.txt"
4) Start the project using "sudo ./run.sh"

## Virtualenv Activation

1) you can install virtualenv by running the following command:
   ```
   sudo -H pip3.9 install virtualenv
   ```
2) To create a new virtual environment with Python 3.9, navigate to the directory where you want to create the environment and run the following command:
   ```
   virtualenv -p python3.9 env
   ```
3) To activate the virtual environment, run the following command:
   ```
   source env/bin/activate
   ```
<h2>Contributers</h2>

 - Amit Kumar Makkad
 - Mihir Karandikar
 
 This project is part of course cs356 Computer Networks Lab IIT Indore. 
