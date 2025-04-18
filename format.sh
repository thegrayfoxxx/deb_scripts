#! /bin/bash

uvx ruff check --fix
uvx ruff check --fix --select I
uvx ruff format
