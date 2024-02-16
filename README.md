# skilzzz

skilzzz is a AWS Demo project that focuses on gathering data about job offers from many sources, mostly in Poland to track value and demand of Data skills.


## Description

scraper-parser relation.
1. scraper need to has `AWS_STEPFUNCTIONS_TASK_TOKEN` env var declared when image is ran. 
This envvar needs to be set in stepfunctions definition of ECS:run task like thatL

```
"Overrides": {
    "ContainerOverrides": [{
        "Name": "justjoinit-scraper",
        "Environment": [{
            "Name": "AWS_STEPFUNCTIONS_TASK_TOKEN",
            "Value.$": "$$.Task.Token"
        }]
    }]
}
```

This is needed so that scraper application can send `send_success` message to step function
when its done. With `output` set to the path that was just created by scraper. Output needs to 
be a valid json-string.

```
send_success(
    token=os.environ['AWS_STEPFUNCTIONS_TASK_TOKEN'],
    output=json.dumps(
        {'output_prefix': session_prefix: str}, default=str
    )
)
```

2. parser need to has `PREFIX` env var declared, to know with folder (prefix) of aws
to parse. For now (as of 2023-11-16) parser can ONLY process one scraper session
at the time. It need to parse `/ts={timestamp}/` partition from given PREFIX to work
correctly.

In step functions output of scraper can be accessed like that:
```
"Overrides": {
    "ContainerOverrides": [{
        "Name": "justjoinit-scraper",
        "Environment": [{
            "Name": "PREFIX",
            "Value.$": "$.output_prefix"
        }]
    }]
}
```


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


## Use selenium standalone application
https://www.browserstack.com/guide/run-selenium-tests-in-docker

docker pull selenium/standalone-chrome
docker run -d -p 4444:4444 -v /dev/shm:/dev/shm selenium/standalone-chrome
sudo docker run -d -e SE_NODE_MAX_SESSIONS=5 -p 4444:4444 -v /dev/shm:/dev/shm selenium/standalone-chrome

password fot vnc (live preview): "secret"

## build

### auth docker with aws cli

aws ecr get-login-password --region eu-central-1 | sudo docker login --username AWS --password-stdin 393861902470.dkr.ecr.eu-central-1.amazonaws.com

### build justjoinit scraper

sudo docker build -t skilzzz-justjoinit-scraper -f skilzzz/Dockerfile.justjoinit-scrape .
sudo docker tag skilzzz-justjoinit-scraper:latest 393861902470.dkr.ecr.eu-central-1.amazonaws.com/skilzzz-justjoinit-scraper:latest
docker push 393861902470.dkr.ecr.eu-central-1.amazonaws.com/skilzzz-justjoinit-scraper:latestu


### build justjoinit parser

sudo docker build -t skilzzz-justjoinit-parse -f skilzzz/Dockerfile.justjoinit-parse .
sudo docker tag skilzzz-justjoinit-parser:latest 393861902470.dkr.ecr.eu-central-1.amazonaws.com/skilzzz-justjoinit-parser:latest
sudo docker push 393861902470.dkr.ecr.eu-central-1.amazonaws.com/skilzzz-justjoinit-parser:latest

"MyTaskToken.$": "$$.Task.Token"

## run locally

### skilzzz-justjoinit-scraper

To run locally:

NEEDED ENV VARS:

- TASK_TOKEN: Stepfunction Callback Task Token. Need to send output to another task.
- SELENIUM_ADDRESS: (Optional, default="localhost:4444") Address to remote selenium server.


# No fluff jobs
1. Use Splash, vet veiwport and use PC useragent