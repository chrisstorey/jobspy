FROM python:3.13-slim

WORKDIR /app
ARG USERNAME=jobspy
ARG USER_UID=1000
ARG USER_GID=$USER_UID

# Create the user
RUN groupadd --gid $USER_GID $USERNAME \
    && useradd --uid $USER_UID --gid $USER_GID -m $USERNAME \
    #
    # [Optional] Add sudo support. Omit if you don't need to install software after connecting.
    && apt-get update \
    && apt-get install -y  -y --no-install-recommends  \
    sudo \
    curl \
    coreutils \
    build-essential \
    && echo $USERNAME ALL=\(root\) NOPASSWD:ALL > /etc/sudoers.d/$USERNAME \
    && chmod 0440 /etc/sudoers.d/$USERNAME \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/

RUN pip install --no-cache-dir -r requirements.txt

COPY main.py /app/
COPY .env_copy /app/.env
RUN chmod +x /app/main.py && mkdir -p /app/data

USER $USERNAME

CMD ["python", "/app/main.py"]
