FROM rust:1.63.0 as build

RUN USER=root cargo new --bin ecowatt-twitter-bot
WORKDIR /ecowatt-twitter-bot

COPY ./Cargo.lock ./Cargo.lock
COPY ./Cargo.toml ./Cargo.toml

RUN cargo build --release && rm src/*.rs
COPY ./src ./src

RUN rm ./target/release/deps/ecowatt_twitter_bot* && cargo build --release

FROM rust:1.63.0-slim

RUN apt-get update && apt-get install -y dialog apt-utils tzdata && \
    rm /etc/localtime && \
    ln -s /usr/share/zoneinfo/Europe/Paris /etc/localtime

COPY --from=build /ecowatt-twitter-bot/target/release/ecowatt-twitter-bot .

CMD ["./ecowatt-twitter-bot"]