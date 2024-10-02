FROM python:3.8-bookworm AS  builder
ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache
WORKDIR /app


# RUN pip config set global.index-url https://mirrors.ustc.edu.cn/pypi/simple
RUN pip install poetry==1.5.1

COPY pyproject.toml poetry.lock ./

RUN --mount=type=cache,target=$POETRY_CACHE_DIR poetry install --no-root

FROM python:3.8-slim-bookworm AS  runtime

ENV VIRTUAL_ENV=/app/.venv \
    PATH="/app/.venv/bin:$PATH"
WORKDIR /app

# RUN sed -i 's/deb.debian.org/mirrors.ustc.edu.cn/g' /etc/apt/sources.list.d/debian.sources
RUN apt update && apt install -y --no-install-recommends  ffmpeg && rm -rf /var/cache/apt/*

COPY --from=builder ${VIRTUAL_ENV} ${VIRTUAL_ENV}
COPY srt_tool ./
RUN sed -i '1i #!/app/.venv/bin/python3' /app/main.py
RUN ln -s /app/main.py /usr/local/bin/dual_sub_tool && chmod a+x /usr/local/bin/dual_sub_tool


CMD ["echo","WARN: invalid usage! please check readme to see how to use"]
