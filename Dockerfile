FROM debian:bookworm-slim as prod

# activate non free components for mscorefonts
RUN sed -i -e's/Components: main/Components: main contrib non-free non-free-firmware/' /etc/apt/sources.list.d/debian.sources

# install needed packages
RUN apt-get -qq update > /dev/null && DEBIAN_FRONTEND=noninteractive apt-get -qq -y --no-install-recommends install \
    dash \
    bash \
    python3 \
    python3-uno \
    python3-pip \
    libreoffice-nogui \
    fonts-liberation \
    ttf-mscorefonts-installer \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# These packages resolve the following warning : "Warning: failed to launch javaldx - java may not function correctly"
# but it does not seem to be needed. All tests pass without it. So it is commented out. (it saves 400Mo for the Docker image)
# RUN apt-get -qq update > /dev/null && DEBIAN_FRONTEND=noninteractive apt-get -qq -y --no-install-recommends install \
#    default-jre \
#    libreoffice-java-common \
#    && apt-get clean \
#    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

RUN useradd -d /app python

COPY . /app
WORKDIR /app

RUN chown python /app -R \
       && pip install -r requirements.txt --break-system-packages

USER python


From prod as dev
USER root
RUN apt-get -qq update > /dev/null && DEBIAN_FRONTEND=noninteractive apt-get -qq -y --no-install-recommends install \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* \


RUN USER=python && \
    GROUP=python && \
    curl -SsL https://github.com/boxboat/fixuid/releases/download/v0.6.0/fixuid-0.6.0-linux-amd64.tar.gz | tar -C /usr/local/bin -xzf - && \
    chown root:root /usr/local/bin/fixuid && \
    chmod 4755 /usr/local/bin/fixuid && \
    mkdir -p /etc/fixuid && \
    printf "user: $USER\ngroup: $GROUP\n" > /etc/fixuid/config.yml

ENTRYPOINT ["fixuid" ]


