# $1 -> website_id (folder name)

cd $1

docker-compose down

docker-compose up --build -d