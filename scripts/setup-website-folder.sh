
# $1 -> website_id
# $2 -> website_code_url
# $3 -> Dockerfile file url for Nodejs
# $4 -> docker-compose.yml file url for designated plan

mkdir $1 # create a folder by website_id

cd $1

# Supabase

wget -O ./$1/website_code.zip $2 # download the website code

unzip ./$1/website_code.zip -d ./$1

wget -O ./$1/Dockerfile $3 # download the Dockerfile for Nodejs

wget -O ./$1/docker-compose.yml $4 # download the docker-compose.yml according to the selected plan

cp ./$1/example.env ./$1/.env # copy the example.env to .env
