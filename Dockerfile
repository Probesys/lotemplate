FROM debian:bookworm-slim as prod
RUN --mount=type=cache,id=apt-cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,id=apt-lib,target=/var/lib/apt,sharing=locked \
    --mount=type=cache,id=debconf,target=/var/cache/debconf,sharing=locked \
	sed -i -e's/Components: main/Components: main contrib non-free/' /etc/apt/sources.list.d/debian.sources \
	&&  echo "Types: deb\nURIs: http://deb.debian.org/debian\nSuites: bookworm-backports\nComponents: main\nSigned-By: /usr/share/keyrings/debian-archive-keyring.gpg" > /etc/apt/sources.list.d/backports.sources \
	&& cat /etc/apt/sources.list.d/backports.sources \
	&& apt update \
	&& apt -y -t bookworm-backports install dash bash python3 python3-uno python3-pip libreoffice-nogui fonts-liberation ttf-mscorefonts-installer \
	&& useradd -d /app python
COPY . /app
WORKDIR /app
RUN chown python /app -R \
       && pip install -r requirements.txt --break-system-packages
USER python


From prod as dev
USER root
RUN --mount=type=cache,id=apt-cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,id=apt-lib,target=/var/lib/apt,sharing=locked \
    --mount=type=cache,id=debconf,target=/var/cache/debconf,sharing=locked \
    apt update && \
    apt install -y curl

RUN USER=python && \
    GROUP=python && \
    curl -SsL https://github.com/boxboat/fixuid/releases/download/v0.6.0/fixuid-0.6.0-linux-amd64.tar.gz | tar -C /usr/local/bin -xzf - && \
    chown root:root /usr/local/bin/fixuid && \
    chmod 4755 /usr/local/bin/fixuid && \
    mkdir -p /etc/fixuid && \
    printf "user: $USER\ngroup: $GROUP\n" > /etc/fixuid/config.yml

ENTRYPOINT ["fixuid" ]


