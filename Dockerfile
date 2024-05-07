FROM ubuntu:focal

ARG DEBIAN_FRONTEND=noninteractive
RUN echo "===> Installing system dependencies..." && \
    apt-get update && \
    apt-get install --no-install-recommends -y python3 python3-pip wget \
    fonts-liberation libappindicator3-1 libasound2 libatk-bridge2.0-0 \
    libnspr4 libnss3 lsb-release xdg-utils libxss1 libdbus-glib-1-2 libgbm1 \
    libu2f-udev curl unzip xvfb;

RUN echo "===> Installing chromedriver..." && \
    wget https://storage.googleapis.com/chrome-for-testing-public/124.0.6367.155/linux64/chromedriver-linux64.zip && \
    unzip chromedriver-linux64.zip -d /usr/bin && \
    mv /usr/bin/chromedriver-linux64/chromedriver /usr/bin/chromedriver && \
    chmod +x /usr/bin/chromedriver && \
    rm chromedriver-linux64.zip;

RUN echo "===> Installing google-chrome..." && \
    CHROME_SETUP=google-chrome.deb && \
    wget -O $CHROME_SETUP "https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb" && \
    dpkg -i $CHROME_SETUP && \
    apt-get install -y -f && \
    rm $CHROME_SETUP;

RUN echo "===> Remove build dependencies..." && \
    apt-get remove -y $BUILD_DEPS && rm -rf /var/lib/apt/lists/*;


ENV LANG C.UTF-8
ENV LC_ALL C.UTF-8
ENV PYTHONUNBUFFERED=1
ENV APP_HOME /usr/src/app

WORKDIR /$APP_HOME
COPY . $APP_HOME/

RUN echo "===> Installing python dependencies..." && \
    pip3 install -r ./requirements.txt;

ENTRYPOINT ["python3", "main.py"]
