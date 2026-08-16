# Down Memory Lane — AI-Powered Childhood Memory Bot

A Slack bot that generates realistic childhood photos of the user from a text prompt, built as a technical assignment for Plivo's Forward Deployed Engineer role.

## What it does

Users type `@MemoryBot my 5-year-old self on a beach` in any Slack channel and get back a photorealistic image of themselves as a child in that scene, within ~45 seconds.

## Architecture

- **Slack** — user interface (via Bolt SDK, Socket Mode — no public server needed)
- **Python bot** (`app.py`) — orchestration layer
- **Replicate** — hosts a fine-tuned Flux.1-dev model with a LoRA adapter trained on 20 photos of the user (~40 MB adapter, 11 min training, ~$2 cost)

## Data flow

1. User `@mentions` the bot with a scene description
2. Bot ACKs within 3s, spawns a background worker
3. Worker builds a prompt with the LoRA's trigger word and calls Replicate
4. Flux + LoRA runs 35 diffusion steps, returns an image URL
5. Bot downloads the image and posts it back into the same Slack thread

## Setup

1. `pip install -r requirements.txt`
2. Create a `.env` file with:
