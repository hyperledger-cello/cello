FROM python:3.13

ENV FABRIC_VERSION=2.5.15

# Install software
RUN apt-get update\
	&& apt-get autoclean\
	&& apt-get clean\
	&& apt-get autoremove\
	&& rm -rf /var/cache/apt/

# Copy source code to the working dir
COPY . .

RUN mkdir cello

# Install compiled code tools from Artifactory and copy it to opt folder.
RUN ARCH=$(dpkg --print-architecture) && \
    case "$ARCH" in \
        amd64|arm64) FABRIC_ARCH="$ARCH" ;; \
        *) echo "Unsupported architecture: $ARCH" >&2; exit 1 ;; \
    esac && \
    curl -fsSL --retry 5 --retry-delay 3 "https://github.com/hyperledger/fabric/releases/download/v${FABRIC_VERSION}/hyperledger-fabric-linux-${FABRIC_ARCH}-${FABRIC_VERSION}.tar.gz" | tar xz -C ./cello/

# Install python dependencies
RUN pip3 install -r requirements.txt

CMD ["python", "manage.py", "runserver", "0.0.0.0:8080"]
