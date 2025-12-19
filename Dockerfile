FROM ghcr.io/graalvm/native-image-community:22


# Install apt on fedora
RUN microdnf install -y ruby graphviz

# Install seafoam
RUN gem install seafoam

RUN microdnf install findutils

RUN python3 -m ensurepip --upgrade

RUN pip3 install pyyaml

# Copy entrypoint script
COPY scripts/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/bin/bash", "/entrypoint.sh"]