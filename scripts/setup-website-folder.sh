mkdir $1 # create a folder by website_id

cd $1

wget -O ./$1/website_code.zip $2 # download the website code

unzip ./$1/website_code.zip -d ./$1

wget -O ./$1/Dockerfile $3 # download the Dockerfile for Nodejs

wget -O ./$1/docker-compose.yml $4 # download the docker-compose.yml according to the selected plan
