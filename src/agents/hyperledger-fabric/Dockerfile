FROM python:3.13

# Install software
RUN apt-get update\
	&& apt-get autoclean\
	&& apt-get clean\
	&& apt-get autoremove\
	&& rm -rf /var/cache/apt/

# Copy source code to the working dir
COPY . .

# Install compiled code tools from Artifactory and copy it to opt folder.
RUN curl -L --retry 5 --retry-delay 3 "https://github.com/hyperledger/fabric/releases/download/v2.5.14/hyperledger-fabric-linux-amd64-2.5.14.tar.gz" | tar xz -C ./cello/

# Install python dependencies
RUN pip3 install -r requirements.txt

CMD ["python", "manage.py", "runserver", "0.0.0.0:8080"]
