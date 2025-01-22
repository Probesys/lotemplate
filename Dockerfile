FROM debian:trixie-slim as prod

RUN rm -f /etc/apt/apt.conf.d/docker-clean; echo 'Binary::apt::APT::Keep-Downloaded-Packages "true";' > /etc/apt/apt.conf.d/keep-cache

RUN --mount=type=cache,id=apt-cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,id=apt-lib,target=/var/lib/apt,sharing=locked \
    --mount=type=cache,id=debconf,target=/var/cache/debconf,sharing=locked \
	sed -i -e's/Components: main/Components: main contrib non-free/' /etc/apt/sources.list.d/debian.sources \
	&& apt update \
    && apt-get -qq update > /dev/null && DEBIAN_FRONTEND=noninteractive apt-get -qq -y --no-install-recommends install \
	dash \
	bash \
	python3 \
	python3-uno \
	python3-pip \
	libreoffice-nogui \
	fonts-liberation \
	ttf-mscorefonts-installer \
	fonts-crosextra-caladea \
	fonts-crosextra-carlito \
	fonts-dejavu \
	fonts-liberation2 \
	fonts-linuxlibertine \
	fonts-noto-core \
	fonts-noto-extra \
	fonts-noto-ui-core \
	fonts-noto-mono \
	fonts-sil-gentium-basic \
	fonts-recommended \
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
    apt-get -qq update > /dev/null && DEBIAN_FRONTEND=noninteractive apt-get -qq -y --no-install-recommends install curl

RUN USER=python && \
    GROUP=python && \
    curl -SsL https://github.com/boxboat/fixuid/releases/download/v0.6.0/fixuid-0.6.0-linux-amd64.tar.gz | tar -C /usr/local/bin -xzf - && \
    chown root:root /usr/local/bin/fixuid && \
    chmod 4755 /usr/local/bin/fixuid && \
    mkdir -p /etc/fixuid && \
    printf "user: $USER\ngroup: $GROUP\n" > /etc/fixuid/config.yml

ENTRYPOINT ["fixuid" ]


