# skilzzz
skilzzz is a AWS Demo project that focuses on gathering data about job offers from many sources, mostly in Poland to track value and demand of Data skills.

## Splash

1. Run docker daemon:
```bash
$ sudo systemctl start docker
```

Start splash:
```bash
$ sudo docker pull scrapinghub/splash
$ sudo docker run -it -p 8050:8050 --rm scrapinghub/splash --disable-private-mode
```


Use selenium standalone application
https://www.browserstack.com/guide/run-selenium-tests-in-docker

docker pull selenium/standalone-chrome
docker run -d -p 4444:4444 -v /dev/shm:/dev/shm selenium/standalone-chrome