#!/usr/bin/bash

cargo build --release --target x86_64-unknown-linux-musl
sudo docker build -t sermerganser/neath:latest . --no-cache

sudo docker container stop neath
sudo docker container rm neath
