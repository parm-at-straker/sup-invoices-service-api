# https://fastapi.tiangolo.com/deployment/docker/
# https://pipenv.pypa.io/en/latest/docker.html

# First build stage - Build venv with pipenv
FROM docker.io/python:3.12-slim-bullseye AS builder

RUN pip install --user pipenv

WORKDIR /build

# Tell pipenv to create venv in the current directory
ENV PIPENV_VENV_IN_PROJECT=1
COPY Pipfile Pipfile.lock /build/
RUN /root/.local/bin/pipenv sync


# Final build stage - Run the app
FROM docker.io/python:3.12-slim-bullseye

WORKDIR /app

# Copy venv from the previous build stage
COPY --from=builder /build/.venv/ /venv/

COPY src src

# Do not run with root
RUN useradd -m -u 1001 -g 33 straker
USER straker

CMD ["/venv/bin/python", "-m", "uvicorn", "src.main:app", "--proxy-headers", "--host", "0.0.0.0", "--port", "80"]
