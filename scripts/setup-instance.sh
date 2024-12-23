echo "nameserver 8.8.8.8" | sudo tee /etc/resolv.conf > /dev/null
echo "nameserver 8.8.4.4" | sudo tee /etc/resolv.conf > /dev/null
echo "127.0.1.1    ubuntu-cloud" | sudo tee -a /etc/hosts

sudo apt update
sudo apt install -y ca-certificates curl gnupg unzip zip htop nano

curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
