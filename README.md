# skilzzz

skilzzz is a AWS Demo project that focuses on gathering data about job offers from many sources, mostly in Poland to track value and demand of Data skills.

## Splash

1. Run docker daemon:

```bash
$ sudo systemctl start docker
out
```

Start splash:

```bash
sudo docker pull scrapinghub/splash
$ sudo docker run -it -p 8050:8050 --rm scrapinghub/splash --disable-private-mode
```


Use selenium standalone application
https://www.browserstack.com/guide/run-selenium-tests-in-docker

docker pull selenium/standalone-chrome
docker run -d -p 4444:4444 -v /dev/shm:/dev/shm selenium/standalone-chrome

## build

### auth docker with aws cli

aws ecr get-login-password --region eu-central-1 | sudo docker login --username AWS --password-stdin 393861902470.dkr.ecr.eu-central-1.amazonaws.com

### build justjoinit scraper

sudo docker build -t skilzzz-justjoinit-scraper -f Dockerfile.justjoinit-scraper .
sudo docker tag skilzzz-justjoinit-scraper:latest 393861902470.dkr.ecr.eu-central-1.amazonaws.com/skilzzz-justjoinit-scraper:latest
docker push 393861902470.dkr.ecr.eu-central-1.amazonaws.com/skilzzz-justjoinit-scraper:latestu


### build justjoinit parser

sudo docker build -t skilzzz-justjoinit-parser -f Dockerfile.justjoinit-parser .
sudo docker tag skilzzz-justjoinit-parser:latest 393861902470.dkr.ecr.eu-central-1.amazonaws.com/skilzzz-justjoinit-parser:latest
sudo docker push 393861902470.dkr.ecr.eu-central-1.amazonaws.com/skilzzz-justjoinit-parser:latest

"MyTaskToken.$": "$$.Task.Token"

## run locally

### skilzzz-justjoinit-scraper

To run locally:

NEEDED ENV VARS:

- TASK_TOKEN: Stepfunction Callback Task Token. Need to send output to another task.
- SELENIUM_ADDRESS: (Optional, default="lokalhost:4444") Address to remote selenium server.
