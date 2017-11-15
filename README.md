1) Install Docker Community Edition
   More information about how to install Docker is available on the Docker website:  https://www.docker.com/community-edition
  
   Note: for the Docker commands in these instructions to work, the Docker daemon must be running. If you do not
   configure it to start automatically, you will need to start it manually before running the Docker commands.
   
   
2) Clone the repository:

   git clone https://github.com/kalamari-proxy/kalamari-proxy.git
   
   Inside the repository, you can run “git checkout v0.1.0” to switch to our code for iteration 2.
   
3) Build the Docker image

4) Inside the Git repository, run:

   docker build . -t test
   
   docker run -p 3128:3128 -p 8080:8080 -t test
   
   
5) Configure your web browser to use the proxy:

   In Firefox 56, the proxy settings can be found in the “preferences” menu at the bottom of the page.
   
   Clicking the “settings” button there will allow you to enter the proxy information.
   
   
6) Within your connection settings, you should configure your proxy by doing the following:

   Select the option to add a manual proxy configuration and set the proxy to 127.0.0.1 on port 3128
   
   Check the box that allows this proxy server to be used on all protocols
   
   In the "No Proxy for" textbox, add:
   
   localhost, 127.0.0.1
   
   
7) Now with docker correctly setup and Firefox being setup to use our proxy, whenever a new connection is made with Firefox we can see it being logged as a new connection with the list (if on any) printed.
