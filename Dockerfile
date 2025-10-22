FROM python:alpine3.22

RUN adduser -D -h /home/librarian -u 1000 -g 1000 librarian

RUN mkdir -p /home/librarian/neath/adapters \
	/home/librarian/neath/cache
	
WORKDIR /home/librarian/neath

COPY ./target/x86_64-unknown-linux-musl/release/neath /home/librarian/neath/neath

COPY --chmod=755 ./adapters ./userscripts ./adapters

RUN chmod +x ./neath && chown -R librarian:librarian /home/librarian

USER librarian

VOLUME ["/home/librarian/neath/cache", "/home/librarian/neath/userscripts"]

EXPOSE 62244

RUN python3 -m pip install bs4 lxml requests
	
CMD ["/home/librarian/neath/neath", "0.0.0.0:62244"]
