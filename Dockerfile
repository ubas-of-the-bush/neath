FROM alpine:3.22.1

RUN adduser -D -h /home/librarian librarian

RUN mkdir -p /home/librarian/neath/adapters \
	/home/librarian/neath/cache

WORKDIR /home/librarian/neath

COPY ./target/x86_64-unknown-linux-musl/release/neath /home/librarian/neath/neath

RUN chmod +x ./neath && chown -R librarian:librarian /home/librarian

VOLUME ["/home/librarian/neath/adapters", "/home/librarian/neath/cache"]

USER librarian

EXPOSE 62244

CMD ["~/neath/neath", "0.0.0.0:62244"]
