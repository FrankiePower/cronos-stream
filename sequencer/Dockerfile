FROM rust:1.88-bullseye AS builder

WORKDIR /app

COPY Cargo.toml ./
COPY src ./src

# Create a dummy main.rs to build dependencies (caching)
# But since we have the source, we can just build directly for now.
# For production we might want to optimize caching.
RUN cargo build --release

FROM debian:bookworm-slim

RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates curl && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY --from=builder /app/target/release/sequencer /app/sequencer

ENV RUST_LOG=info

EXPOSE 4001

CMD ["/app/sequencer"]
