# cs356-networking
A Ryu based SDN (Software defined Networking) controller to implement switch circuiting using SPF (Shortest Path First) algorithm.

1. Create a custom topology of 10 nodes (except linear or bus).
2. Randomly select the link delay (1ms – 5ms) for all links in your topology between the switches. Set link bandwidth to 50Mb.
3. Write a program to discover the topology, including the switches and hosts in the network.
4. Run a client-server program at a pair of hosts to identify the link cost based on the time it takes to traverse the link.
5. Use the above information for computing the paths in the network for all pairs of hosts in the network. Take user input to request the connection by asking for following:
* Source and destination host
* Service requests are either IPv4 or MAC based
* Bandwidth of the service (1-5Mb)

6. Identify the switches where configuration need to be updated. Provide details of the configuration to be written over each intermediate switch on the path.
7. Include the already configured services in path computation. You need to keep track of the available bandwidth of the links (how much utilized, how much unutilized)
Based on the delay and available bandwidth information compute the new cost for the link. Cost will be updated with changes in the available bandwidth.
8. Repeat from step 5 till user gives input.

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
