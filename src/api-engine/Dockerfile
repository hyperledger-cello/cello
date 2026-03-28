FROM python:3.8

# Install software
RUN apt-get update\
	&& apt-get install -y gettext-base graphviz libgraphviz-dev vim\
	&& apt-get autoclean\
	&& apt-get clean\
	&& apt-get autoremove\
	&& rm -rf /var/cache/apt/

# Copy source code to the working dir
COPY . .

# Install python dependencies
RUN pip3 install -r requirements.txt

# Install go
ENV GO_VERSION=1.25.5
RUN wget https://go.dev/dl/go${GO_VERSION}.linux-amd64.tar.gz \
    && tar -C /usr/local -xzf go${GO_VERSION}.linux-amd64.tar.gz \
    && rm go${GO_VERSION}.linux-amd64.tar.gz
ENV PATH="${PATH}:/usr/local/go/bin"

CMD ["bash", "entrypoint.sh"]
