FROM debian:bullseye as prod
RUN --mount=type=cache,id=apt-cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,id=apt-lib,target=/var/lib/apt,sharing=locked \
    --mount=type=cache,id=debconf,target=/var/cache/debconf,sharing=locked \
	sed -i -e's/ main/ main contrib non-free/g' /etc/apt/sources.list \
	&& echo 'deb http://deb.debian.org/debian bullseye-backports main' > /etc/apt/sources.list.d/backports.list \
	&& apt update \
	&& apt -y -t bullseye-backports install dash bash python3 python3-uno python3-pip libreoffice-nogui fonts-liberation ttf-mscorefonts-installer \
	&& useradd -d /app python
COPY . /app
WORKDIR /app
RUN chown python /app -R \
       && pip install -r requirements.txt
USER python
