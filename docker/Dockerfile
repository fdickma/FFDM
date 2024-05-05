FROM python:3.11-slim

ARG DOCKER_USER=ffdm_user
ARG DOCKER_USER_ID=2000
RUN addgroup --gid $DOCKER_USER_ID --group $DOCKER_USER
RUN adduser --uid $DOCKER_USER_ID --gid $DOCKER_USER_ID --system --no-create-home $DOCKER_USER

WORKDIR /ffdm

RUN apt-get update && \
    apt-get install -y locales && \
    sed -i -e 's/# de_DE.UTF-8 UTF-8/de_DE.UTF-8 UTF-8/' /etc/locale.gen && \
    sed -i -e 's/# de_DE.8859-1/de_DE.8859-1/' /etc/locale.gen && \
    sed -i -e 's/# en_US.UTF-8 UTF-8/en_US.UTF-8 UTF-8/' /etc/locale.gen && \
    sed -i -e 's/# en_US.8859-1/en_US.8859-1/' /etc/locale.gen && \
    sed -i -e 's/# en_US.8859-15 ISO-8859-15/en_US.8859-15 ISO-8859-15/' /etc/locale.gen && \
    dpkg-reconfigure --frontend=noninteractive locales
ENV LANG en_US.UTF-8
ENV LC_ALL en_US.UTF-8
RUN apt-get install -y gcc sqlite3 w3m cron sudo tzdata && \
    ln -fs /usr/share/zoneinfo/Europe/Berlin /etc/localtime && \
    dpkg-reconfigure --frontend noninteractive tzdata
RUN usermod -aG sudo $DOCKER_USER
RUN echo '%sudo ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers
COPY ./crontab /etc/crontab
RUN sed -i 's:ffdm_user:'"${DOCKER_USER}"':g' /etc/crontab

COPY ./py_requirements.txt py_requirements.txt
RUN pip install --no-cache-dir --upgrade -r py_requirements.txt

RUN mkdir /ssl
RUN mkdir /var/cache/matplotlib
COPY ffdm/ /ffdm/
RUN chown $DOCKER_USER:$DOCKER_USER /ffdm -R
RUN chown $DOCKER_USER:$DOCKER_USER /ssl -R
RUN chown $DOCKER_USER:$DOCKER_USER /var/cache/matplotlib -R

USER $DOCKER_USER
ENV FLASK_APP ffdm_app:app
ENV port 8811
ENV certfile /ssl/certfile.crt
ENV keyfile /ssl/keyfile.key
ENV MPLCONFIGDIR=/var/cache/matplotlib

EXPOSE ${port}
ENTRYPOINT sudo sed -i 's:mfreq:'"${MFREQ}"':g' /etc/crontab && \
sudo sed -i 's:wwmin:'"${WWMIN}"':g' /etc/crontab && \
sudo sed -i 's:wemin:'"${WEMIN}"':g' /etc/crontab && \
sudo /etc/init.d/cron start & \
gunicorn --reload --workers 1 --timeout 180 --bind 0.0.0.0:${port} --certfile ${certfile} --keyfile ${keyfile} ffdm_app:app
