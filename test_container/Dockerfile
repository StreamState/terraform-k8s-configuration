ARG NODE_VERSION=12.18.3

FROM node:${NODE_VERSION}
ARG version=latest
WORKDIR /home/theia
ADD $version.package.json ./package.json
ARG GITHUB_TOKEN
RUN yarn --pure-lockfile && \
  NODE_OPTIONS="--max_old_space_size=4096" yarn theia build && \
  yarn theia download:plugins && \
  yarn --production && \
  yarn autoclean --init && \
  echo *.ts >> .yarnclean && \
  echo *.ts.map >> .yarnclean && \
  echo *.spec.* >> .yarnclean && \
  yarn autoclean --force && \
  yarn cache clean

FROM us-central1-docker.pkg.dev/streamstatetest/streamstatetest/pysparkbase:v0.3.0
USER root
RUN apt-get update
RUN apt-get install -y curl libsecret-1-dev
RUN curl -sL https://deb.nodesource.com/setup_12.x -o nodesource_setup.sh
RUN bash nodesource_setup.sh
RUN apt-get install -y nodejs
RUN mkdir -p /home/theia 
RUN mkdir -p /home/sparkpy 
ADD run.sh /home/sparkpy/run.sh
ADD main.py /home/sparkpy/main.py
ADD process.py /home/sparkpy/process.py
ENV HOME /home/sparkpy
ADD example.json /home/sparkpy/example.json
WORKDIR /home/theia
COPY --from=0 /home/theia /home/theia
EXPOSE 3000
RUN chown -R sparkpy:sparkpy $HOME
USER sparkpy
ENV SHELL=/bin/bash \
  THEIA_DEFAULT_PLUGINS=local-dir:/home/theia/plugins
ENV USE_LOCAL_GIT true
ENTRYPOINT [ "node", "/home/theia/src-gen/backend/main.js", "/home/sparkpy", "--hostname=0.0.0.0" ]
#CMD /home/theia/run.sh