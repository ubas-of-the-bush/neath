FROM rust:1.90-alpine3.20 AS build

WORKDIR /build

COPY Cargo.toml config.toml .

COPY ./src/ ./src

RUN apk add musl-dev

RUN cargo build --release

FROM python:alpine3.22

RUN adduser -D -h /home/librarian -u 1000 -g 1000 librarian

RUN mkdir -p /home/librarian/neath/adapters \
	/home/librarian/neath/cache
	
WORKDIR /home/librarian/neath

COPY --from=build /build/target/release/neath /home/librarian/neath/neath

COPY --chmod=755 ./adapters ./userscripts ./adapters

COPY ./env ./env

RUN chmod +x ./neath && chown -R librarian:librarian /home/librarian

USER librarian

VOLUME ["/home/librarian/neath/cache", "/home/librarian/neath/userscripts", "/home/librarian/neath/env"]

EXPOSE 62244

RUN python3 -m pip install bs4 lxml requests
	
CMD ["/home/librarian/neath/neath", "0.0.0.0:62244"]
